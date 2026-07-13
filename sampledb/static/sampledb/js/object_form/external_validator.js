/**
 * Handle Validate button clicks for all external_validator fields via event
 * delegation. This automatically covers fields that are added dynamically
 * (e.g. inside array containers).
 *
 * NOTE: this only provides instant feedback while editing. It is not the
 * authoritative check -- the server re-validates via the same external
 * service when the object is actually saved, ignoring these hidden inputs.
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

  const validator = button.dataset.validator || '';
  const text = textInput ? textInput.value : '';

  const csrfTokenEl = document.querySelector('input[name="csrf_token"]');
  const csrfToken = csrfTokenEl ? csrfTokenEl.value : '';
  const applicationRootPath = window.getTemplateValue('application_root_path');

  button.disabled = true;
  if (statusDiv) {
    statusDiv.innerHTML = '<span class="text-muted"><i class="fa fa-spinner fa-spin"></i> Validating\u2026</span>';
  }

  try {
    const body = new FormData();
    body.append('validator', validator);
    body.append('text', text);
    body.append('csrf_token', csrfToken);

    const response = await fetch(applicationRootPath + 'objects/external_validator_proxy', {
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

/**
 * Clear any previous (now stale) validation result whenever the text changes,
 * so the UI never shows a "Valid" checkmark for text that hasn't actually
 * been re-checked.
 */
function handleExternalValidatorInput (e) {
  const textInput = e.target.closest('[data-external-validator-input]');
  if (!textInput) return;
  const container = textInput.closest('[data-external-validator-container]');
  if (!container) return;
  const isValidInput = container.querySelector('[data-external-validator-is-valid]');
  const validatedTextInput = container.querySelector('[data-external-validator-validated-text]');
  const statusDiv = container.querySelector('[data-external-validator-status]');
  if (isValidInput) isValidInput.value = '';
  if (validatedTextInput) validatedTextInput.value = '';
  if (statusDiv) statusDiv.innerHTML = '';
}

function setupExternalValidatorButtons () {
  document.removeEventListener('click', handleExternalValidatorClick);
  document.addEventListener('click', handleExternalValidatorClick);
  document.removeEventListener('input', handleExternalValidatorInput);
  document.addEventListener('input', handleExternalValidatorInput);
}

document.addEventListener('DOMContentLoaded', setupExternalValidatorButtons);

export { setupExternalValidatorButtons, handleExternalValidatorClick, handleExternalValidatorInput };