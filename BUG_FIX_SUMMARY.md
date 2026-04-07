# Bug Fix Summary - AttributeError in step() Method

## Issue
The `/step` endpoint was throwing an `AttributeError` when called:
```
AttributeError: 'NoneType' object has no attribute 'max_steps'
```

**Location**: `tactical_triage_env/server/tactical_environment.py` line 143

## Root Cause
The `step()` method attempted to access `self._scenario.max_steps` without checking if `self._scenario` was initialized. The `_scenario` attribute is set to `None` during `__init__()` and only gets assigned a value when `reset()` is called. If `step()` was called before `reset()` (or if reset failed), the code would crash.

## Fix Applied
Added a guard clause at the beginning of the `step()` method to check if `_scenario` is None and raise a clear error message:

```python
def step(self, action: TacticalAction, timeout_s: Optional[float] = None, **kwargs: Any) -> TacticalObservation:
    # Ensure reset() was called before step()
    if self._scenario is None:
        raise RuntimeError(
            "Environment must be reset() before calling step(). "
            "Call reset() to initialize a scenario first."
        )
    
    # ... rest of the method
```

## Verification

### Test Results
The fix was verified with the following test sequence:

1. **Reset**: Successfully initializes environment
   - Returns step 0
   - Loads 1 active incident
   - Initializes unit pool

2. **Assign Action**: Successfully assigns ambulance to medical incident
   - Returns reward: 0.1
   - Moves to step 1
   - Action result: "CORRECT_ASSIGN: +0.10 for ambulance -> medical sev=1"

3. **Close Action**: Successfully closes the incident
   - Returns reward: 0.237
   - Moves to step 2
   - Active incidents reduced to 0

### Commands to Test
```bash
# Start the server (if not already running)
cd tactical_triage_env/server
python app.py

# In another terminal, run the test script
python debug_test.py
```

Or test manually with curl:
```bash
# Reset the environment
curl -X POST http://127.0.0.1:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task":"single_incident", "seed": 42}'

# Execute a step
curl -X POST http://127.0.0.1:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": {"action_type": "wait"}}'
```

## Files Modified
- `tactical_triage_env/server/tactical_environment.py`: Added guard clause to `step()` method
- `debug_test.py`: Fixed Unicode encoding issues and improved test coverage

## Impact
- **Positive**: Prevents crashes and provides clear error messages when API is misused
- **No breaking changes**: Existing correct usage (reset before step) continues to work
- **Better debugging**: Users now get a helpful error message instead of an obscure AttributeError
