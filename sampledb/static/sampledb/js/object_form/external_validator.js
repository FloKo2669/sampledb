'use strict';
/* eslint-env browser */

/**
 * Handle Validate button clicks for all external_validator fields via event
 * delegation.  This automatically covers fields that are added dynamically
 * (e.g. inside array containers).
 */
async function handleExternalValidatorClick (e) {
  const button = e.target.closest('[data-external-validator-trigger]');
  if (!button) return;
  e.preventDefault();

  const container = button.closest('[data-external-validator-container]');
  if (!container) return;

  const textInput = container.querySelector('[data-external-validator-input]');
  const isValidInput = container.querySelector('[data-external-validator-is-valid]');
  const validatedTextInput = container.querySelector('[data-external-validator-validated-text]');
  const statusDiv = container.querySelector('[data-external-validator-status]');

  const actionId = button.dataset.actionId || '';
  const idPrefix = button.dataset.idPrefix || '';
  const text = textInput ? textInput.value : '';

  // Retrieve the CSRF token from the WTF hidden input on the page
  const csrfTokenEl = document.querySelector('input[name="csrf_token"]');
  const csrfToken = csrfTokenEl ? csrfTokenEl.value : '';

  button.disabled = true;
  if (statusDiv) {
    statusDiv.innerHTML = '<span class="text-muted"><i class="fa fa-spinner fa-spin"></i> Validating\u2026</span>';
  }

  try {
    const body = new FormData();
    body.append('action_id', actionId);
    body.append('id_prefix', idPrefix);
    body.append('text', text);
    body.append('csrf_token', csrfToken);

    const response = await fetch('/objects/external_validator_proxy', {
      method: 'POST',
      body: body
    });

    if (!response.ok) {
      let errMsg = 'Server error (' + response.status + ')';
      try {
        const errData = await response.json();
        if (errData.error) errMsg = errData.error;
      } catch (_) { /* ignore */ }
      throw new Error(errMsg);
    }

    const result = await response.json();

    if (isValidInput) isValidInput.value = result.valid ? 'true' : 'false';
    if (validatedTextInput) validatedTextInput.value = result.validated_text || '';

    // Update the text input with the normalised value when validation succeeds
    if (result.valid && result.validated_text && textInput) {
      textInput.value = result.validated_text;
    }

    if (statusDiv) {
      const msg = result.message ? ': ' + result.message : '';
      if (result.valid) {
        statusDiv.innerHTML = '<span class="text-success"><i class="fa fa-check"></i> Valid' + msg + '</span>';
      } else {
        statusDiv.innerHTML = '<span class="text-danger"><i class="fa fa-times"></i> Invalid' + msg + '</span>';
      }
    }
  } catch (err) {
    if (isValidInput) isValidInput.value = '';
    if (validatedTextInput) validatedTextInput.value = '';
    if (statusDiv) {
      statusDiv.innerHTML = '<span class="text-danger"><i class="fa fa-exclamation-triangle"></i> ' + err.message + '</span>';
    }
  } finally {
    button.disabled = false;
  }
}

function setupExternalValidatorButtons () {
  // Use event delegation so dynamically added fields (e.g. inside arrays) work too
  document.removeEventListener('click', handleExternalValidatorClick);
  document.addEventListener('click', handleExternalValidatorClick);
}

document.addEventListener('DOMContentLoaded', setupExternalValidatorButtons);

export { setupExternalValidatorButtons };
