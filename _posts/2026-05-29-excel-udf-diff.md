---
layout: post
categories: ["Excel", "VBA", "UDF"]
---

# Using Excel UDF to compare data differences

Excel is still one of the best tools for ad-hoc analysis when you're not dealing with a huge amount of data. A common task is comparing two versions of data and highlighting the differences. Here I'll use this scenario to demonstrate how we can use a VBA User Define Function (UDF) to do exactly that and extend the idea for other tasks as well.

## The hacking approach
The main limitation of UDFs is that they are not allowed to change anything in Excel, such as modifying cell formatting or changing values in other cells. Excel treats them strictly as "formula functions" rather than full macros.

To bypass this limitation, we can use a bit of a hack. In this case, I rely on `Application.Evaluate("FunctionNameToBeCalled()")`, which is much simpler compared with other methods.

Because of how this hack operates, we have to split the logic into two functions:
- The first acts as a wrapper UDF
- The second performs the actual work

Since function parameters cannot be passed reliably into the second function via `Application.Evaluate`, we store them in module-level global variables and access them in the helper function.

## The implementation details

### Global variables
First, define the global variables at the top of the module to hold the arguments temporarily:
```vb
' Global parameters to pass ranges to the evaluator helper
Private Diff_Rng1 As Range
Private Diff_Rng2 As Range
Private Diff_Tolv As Double
```

### First function (UDF wrapper)
This is the public UDF that will actually be called from the Excel worksheet formulas:
```vb
' The Public UDF used in Excel formulas
Public Function RngDiff(rng1 As Range, rng2 As Range, Optional tol As Double = 0.0001) As String
    ' Check for size mismatch instantly
    If rng1.Rows.Count <> rng2.Rows.Count Or rng1.Columns.Count <> rng2.Columns.Count Then
        RngDiff = "SIZE_DIFF"
        Exit Function
    End If

    ' Assign ranges to module-level pseudo-parameters
    Diff_Tolv = tol
    Set Diff_Rng1 = rng1
    Set Diff_Rng2 = rng2

    ' Trigger the evaluation hack and return result ("SAME" or "DIFF")
    RngDiff = Application.Evaluate("CheckAndMarkRngDiff()")
End Function
```

### Second function (helper logic)
This is the private helper function that checks the differences and executes the formatting changes, effectively bypassing Excel's UDF restrictions:
```vb
' The Private Helper Function that bypasses Excel's UDF blockages
Private Function CheckAndMarkRngDiff() As String
    Dim tol As Double
    Dim r As Long, c As Long
    Dim hasDiff As Boolean
    Dim isDiff As Boolean
    Dim arr1 As Variant, arr2 As Variant
    Dim val1 As Variant, val2 As Variant

    ' Clear existing background colors safely
    Diff_Rng1.Interior.ColorIndex = xlNone
    Diff_Rng2.Interior.ColorIndex = xlNone

    ' Read ranges once
    arr1 = Diff_Rng1.Value2
    arr2 = Diff_Rng2.Value2

    ' Loop through and compare cells
    hasDiff = False
    tol = Diff_Tolv
    For r = 1 To UBound(arr1, 1)
        For c = 1 To UBound(arr1, 2)
            val1 = arr1(r, c)
            val2 = arr2(r, c)

            isDiff = False
            If IsEmpty(val1) Xor IsEmpty(val2) Then
                isDiff = True        ' 1. Empty check
            ElseIf IsNumeric(val1) And IsNumeric(val2) Then
                If Abs(val1 - val2) > tol Then
                    isDiff = True    ' 2. Numeric with tolerance
                End If
            ElseIf val1 <> val2 Then
                isDiff = True        ' 3. Standard Text/Variant Comparison
            End If

            If isDiff Then
                hasDiff = True
                ' Only now touch sheet
                Diff_Rng1.Cells(r, c).Interior.Color = RGB(255, 200, 200) ' Light Red
                Diff_Rng2.Cells(r, c).Interior.Color = RGB(255, 200, 200)
            End If
        Next c
    Next r

    ' Return the final status back to the parent UDF
    If hasDiff Then
        CheckAndMarkRngDiff = "DIFF"
    Else
        CheckAndMarkRngDiff = "SAME"
    End If
End Function
```

## Performance notes
Note that I already includes a performance optimization: reading the values of both ranges into arrays first. That avoids expensive cell-by-cell communication with the worksheet during comparisons.

For larger datasets, further improvements include:
- Disabling calculation
- Disabling events
- Turning off screen updating

These should be done before execution and restored afterward to avoid side effects and improve performance significantly.

## How to use the custom UDF
To reuse this UDF in any of your Excel files, package it into a custom Excel Add-in (`.xlam`) and enable it in your Excel Add-ins.

When you need to compare the two different versions of your data, whether they are on the same worksheet or different Excel files, simply select an empty cell and enter the formula:
```
=RngDiff(Range1,Range2)
```
Then press the `Enter` button to run the comparison. You can also select ranges using the mouse while building the formula.

Once the comparison is done, you may delete the formula cell to avoid any unintended recalculation side effects.

If you're interested in more custom VBA utilities, check out my GitHub page: [seanslma](https:github.com/seanslma).

## References
- [https://stackoverflow.com/questions/12501759/vba-update-other-cells-via-user-defined-function](https://stackoverflow.com/questions/12501759/vba-update-other-cells-via-user-defined-function)
