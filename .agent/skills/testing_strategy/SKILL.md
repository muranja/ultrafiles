---
name: testing_rails
description: Mandatory testing patterns and requirements for all new features.
---

# Testing Rails

> [!IMPORTANT]
> No feature is complete without tests passing these rails.

## 1. Test Location & Naming

- **Unit Tests**: `tests/unit/test_<module_name>.py`
- **Integration Tests**: `tests/integration/test_<flow_name>.py`
- **UI Tests**: `tests/ui/test_<window_name>.py`

## 2. Unit Test Rails

- **Isolation**:
  - **MUST** mock all external dependencies (`Gio.File`, `subprocess`, `vte`).
  - **MUST** use `unittest.mock.MagicMock` for GTK widgets to avoid display requirement.
- **Coverage**:
  - **MUST** test both Success and Failure paths.
  - **MUST** test edge cases (empty strings, None, large inputs).

## 3. Async Testing Rails

- **Pattern**:
  - **MUST** use the `GLib.MainLoop` pattern for async signals:

    ```python
    def test_async_op():
        loop = GLib.MainLoop()
        result = {}
        def callback(obj, res):
            result['data'] = obj.finish(res)
            loop.quit()
        
        obj.async_method(callback)
        loop.run() # potentially with timeout
        assert result['data'] == expected
    ```

## 4. UI Test Rails

- **Accessibility**:
  - **MUST** ensure all interactive widgets have `tooltip-text` or `accessible-role`.
  - **SHOULD** use `dogtail` to verify UI state via accessibility tree.
