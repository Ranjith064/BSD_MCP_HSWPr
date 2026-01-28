# Info on Splitter file handling
Here all the needed for the handling the splitter file for this Failsafe part will be explained
Splitter file use the extension .xml

## Useful info Keywords and their significance
> Each Failure word properties Start from keyword `<FAILURE_WORD>` and Ends with `</FAILURE_WORD>`
> `<SHORT-NAME>` represents the Failure word name 
> `<DESCRIPTION>` represents the Monitoring purpose 
> `<GOOD_CHECK_DESCRIPTION>` represents info on the Good Check approach 
> `<ROOTCAUSE>` represents the Monitoring Logic or the failure use case 


## Filter Time Configurations Details

> Filter time configuration in the splitter file is based on the Autosar Daimant tool 

### Example Configuration Structure
The configuration for the counter will look similar to the example provided:

```xml
<AUTOSAR>
    <EventPriority>255</EventPriority>
    <DebouncerAlgorithm>
        <DebouncerType>CounterBased</DebouncerType>
        <DebouncerTimebased>
            <DebouncetimeFailedthreshold />
            <DebouncetimePassedthreshold />
        </DebouncerTimebased>
        <DebouncerCounterbased>
            <DebouncecounterIncrementstepsize>1</DebouncecounterIncrementstepsize>
            <DebouncecounterDecrementstepsize>1</DebouncecounterDecrementstepsize>
            <DebouncecounterFailedthreshold>6</DebouncecounterFailedthreshold>
            <DebouncecounterPassedthreshold>-1</DebouncecounterPassedthreshold>
            <DebouncecounterJumpup />
            <DebouncecounterJumpdown />
            <DebouncecounterJumpdownvalue />
            <DebouncecounterJumpupvalue />
        </DebouncerCounterbased>
    </DebouncerAlgorithm>
</AUTOSAR>
```

### Determining Counter Type

To understand whether the Monitoring or Failure word uses Autosar based counter or internal counter, refer to data in `<DebouncerType>` within the failure word configuration properties:

- **`CounterBased`** → Autosar based debounce counter
- **`MonitoringInternal`** → Counter is defined in the monitoring logic file itself

### Filter Time Calculation for CounterBased Type

When `<DebouncerType>` is `CounterBased`, follow these steps:

#### Step 1: Extract Required Data
Get the following data from the corresponding Failure word properties defined in splitter file:

1. **Task_Cycle** = data in `<TASK_REF>` (data in milliseconds)
2. **JumpUpState** = data in `<DebouncecounterJumpup>`
3. **JumpDownState** = data in `<DebouncecounterJumpdown>`
4. **IncrementStep** = data in `<DebouncecounterIncrementstepsize>`
5. **DecrementStep** = data in `<DebouncecounterDecrementstepsize>`
6. **Fail_Threshold** = data in `<DebouncecounterFailedthreshold>`
7. **Pass_Threshold** = data in `<DebouncecounterPassedthreshold>`
8. **JumpUpValue** = data in `<DebouncecounterJumpupvalue>` (provides info on which number the counter will start incrementing once the fail condition is met)
9. **JumpDownValue** = data in `<DebouncecounterJumpdownvalue>` (provides info from which number the counter will start decrementing once the pass condition is met)

#### Step 2: Apply Calculation Formulas

Once the data is available, use the below formulas to calculate the filter time:

##### 1. Failure Filter Time
First calculate the total steps needed:
```
IF (JumpUpState == TRUE)
{
    StepsNeeded = (Fail_Threshold - JumpUpValue) / IncrementStep
}
else
{
    StepsNeeded = (Fail_Threshold - Pass_Threshold) / IncrementStep
}

Failure_FilterTime = Task_Cycle × StepsNeeded
```

##### 2. Recovery Filter Time
First calculate the total steps needed:
```
IF (JumpDownState == TRUE)
{
    StepsNeeded = (JumpDownValue - Pass_Threshold) / DecrementStep
}
else
{
    StepsNeeded = (Fail_Threshold - Pass_Threshold) / DecrementStep
}

Recovery_FilterTime = Task_Cycle × StepsNeeded
```

# ************Updated By Copilot**********************************************************

## CRITICAL LESSONS LEARNED & BEST PRACTICES 

### ⚠️ MANDATORY CALCULATION METHODOLOGY

**ALWAYS use the formulas above for timing calculations - NEVER rely on embedded XML comments!**

During MonitoringDifferenceAnalysis execution for RBBLS component (FW_RBBrakeLightSwitchLineInterrupt), it was discovered that:

1. **XML embedded comments can be INCORRECT or OUTDATED**
   - Example: `<ITEM key="RecoveryTime">505 ms</ITEM>` comment was found to be inaccurate
   - The actual recovery time calculated using proper formulas was 500ms (0.5 seconds)

2. **JumpDown state verification is CRITICAL**
   - Always check actual XML configuration: `<DebouncecounterJumpdown>TRUE</DebouncecounterJumpdown>`
   - Do NOT assume JumpDown=FALSE without verification
   - This directly affects which formula branch to use for recovery time calculation

### 📋 EXECUTION CHECKLIST FOR MonitoringDifferenceAnalysis

When performing `/MonitoringDifferenceAnalysis`:

✅ **Step 1**: Extract actual XML configuration values (not comments)
✅ **Step 2**: Verify JumpUp/JumpDown states from XML tags
✅ **Step 3**: Apply formulas exactly as documented above
✅ **Step 4**: Cross-validate calculations with actual configuration changes
✅ **Step 5**: Document any discrepancies between comments and calculated values

### 🔍 EXAMPLE: RBBLS Configuration Analysis

**Target Configuration (rbbutswi_new):**
- DebouncecounterFailedthreshold: 100
- DebouncecounterPassedthreshold: -1
- DebouncecounterJumpdownvalue: 99
- DebouncecounterJumpdown: TRUE
- Task_Cycle: 5ms

**Correct Recovery Time Calculation:**
```
JumpDownState == TRUE, so:
StepsNeeded = (JumpDownValue - Pass_Threshold) / DecrementStep
StepsNeeded = (99 - (-1)) / 1 = 100 steps
Recovery_FilterTime = 5ms × 100 = 500ms = 0.5 seconds
```

**Reference Configuration (rbbutswi_old):**
- DebouncecounterFailedthreshold: 600
- DebouncecounterPassedthreshold: -600
- DebouncecounterJumpdownvalue: 0
- DebouncecounterJumpdown: TRUE

**Correct Recovery Time Calculation:**
```
JumpDownState == TRUE, so:
StepsNeeded = (JumpDownValue - Pass_Threshold) / DecrementStep
StepsNeeded = (0 - (-600)) / 1 = 600 steps
Recovery_FilterTime = 5ms × 600 = 3000ms = 3.0 seconds
```

**Result**: 6x improvement in recovery time (3.0s → 0.5s)

### 🚨 COMMON PITFALLS TO AVOID

1. **DO NOT** use embedded XML comments for timing calculations
2. **DO NOT** assume JumpDown=FALSE without checking XML configuration
3. **DO NOT** skip formula verification when configuration changes are detected
4. **DO NOT** rely on previous assumptions - always verify current XML state

### 📝 DOCUMENTATION REQUIREMENTS

When updating failsafe documentation after MonitoringDifferenceAnalysis:
- Highlight timing improvements/changes in **red text**
- Include both old and new calculated values
- Reference the specific XML configuration changes
- Document the calculation methodology used
- Note any discrepancies found between comments and actual calculations
- **Generate professional failsafe output file** following `Output_format.md` standard table format
- **Create `[Component]_FailSafe.md`** file with calculated timing values in the Output directory