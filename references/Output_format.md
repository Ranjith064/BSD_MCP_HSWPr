# Output Format Reference
    Below section shows an example format how the Final output should be and Name of the file should be as per the example " BLS_FailSafe.md"


## BLS Line Monitoring

| **Attribute** | **Details** |
|:--------------|:------------|
| **Purpose** | Detecting BLS line failure. |
| **Detection Condition** | **ESP:** If the BLS line voltage is higher than 0.219×UBVR and lower than 0.71×UBVR continuously, the failure is detected.<br><br>**ESPHev:** If the BLS line voltage is higher than 0.219×UBVR and lower than 0.71×UBVR continuously, the failure is detected. |
| **Detection Time** | 3s. |
| **Monitoring Period** | Continuous. |
| **Recovery Condition** | After ignition cycle, the failure condition is not met for 3s. |
| **Note** | Applicable for all projects but in ESPHevX projects, the failure will not result in any shutdown. |

## Show the change content in the respective area with struck out font and Print only the data as mentioned above

## Use Red color for the old value and Green for new value 