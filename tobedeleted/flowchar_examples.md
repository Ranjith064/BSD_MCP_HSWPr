# Example: If-Else Statement Flowchart (Mermaid)

```mermaid
graph TD
    start([Start])
    decision1{Is x > 0?}
    action1[Set y = 1]
    action2[Set y = -1]
    end_node([End])

    start --> decision1
    decision1 -- Yes --> action1
    decision1 -- No --> action2
    action1 --> end_node
    action2 --> end_node
```

// C code for reference:
// if (x > 0) {
//     y = 1;
// } else {
//     y = -1;
// }

# Example: While Loop Flowchart (Mermaid)

```mermaid
graph TD
    start2([Start])
    loop1{Is x < 10?}
    action3[Increment x]
    end_node2([End])

    start2 --> loop1
    loop1 -- Yes --> action3
    action3 --> loop1
    loop1 -- No --> end_node2
```

// C code for reference:
// while (x < 10) {
//     x++;
// }

# Example: For Loop Flowchart (Mermaid)

```mermaid
graph TD
    start3([Start])
    loop2{Is i < 5?}
    action4[Process i]
    action5[Increment i]
    end_node3([End])

    start3 --> loop2
    loop2 -- Yes --> action4
    action4 --> action5
    action5 --> loop2
    loop2 -- No --> end_node3
```

// C code for reference:
// for (int i = 0; i < 5; i++) {
//     // Process i
// }

# Example: Switch Statement Flowchart (Mermaid)

```mermaid
graph TD
    start4([Start])
    switch1{Value of x}
    case1[Case 1: ...]
    case2[Case 2: ...]
    caseDefault[Default: ...]
    end_node4([End])

    start4 --> switch1
    switch1 -- 1 --> case1
    switch1 -- 2 --> case2
    switch1 -- default --> caseDefault
    case1 --> end_node4
    case2 --> end_node4
    caseDefault --> end_node4
```

// C code for reference:
// switch (x) {
//   case 1:
//     // ...
//     break;
//   case 2:
//     // ...
//     break;
//   default:
//     // ...
// }