Attribute VB_Name = "Module1"
Sub SolverMacro()
Attribute SolverMacro.VB_ProcData.VB_Invoke_Func = " \n14"

' SolverMacro Macro
    
    SolverReset
    
    Sheets("Edge1").Select
    SolverAdd CellRef:="$D$7", Relation:=1, FormulaText:="1000"
    SolverAdd CellRef:="$D$7", Relation:=3, FormulaText:="1+0.0000000001"
    SolverAdd CellRef:="$D$11", Relation:=1, FormulaText:="1.2"
    SolverOk SetCell:="$D$22", MaxMinVal:=2, ValueOf:=40, ByChange:="$D$7", Engine _
        :=1, EngineDesc:="GRG Nonlinear"
    SolverSolve (True)
    SolverSolve userFinish:=True
    SolverFinish KeepFinal:=1
    
        
    Sheets("Edge4").Select
    SolverAdd CellRef:="$D$7", Relation:=1, FormulaText:="1000"
    SolverAdd CellRef:="$D$7", Relation:=3, FormulaText:="1+0.0000000001"
    SolverAdd CellRef:="$D$11", Relation:=1, FormulaText:="1.2"
    SolverOk SetCell:="$D$22", MaxMinVal:=2, ValueOf:=40, ByChange:="$D$7", Engine _
        :=1, EngineDesc:="GRG Nonlinear"
    SolverSolve (True)
    SolverSolve userFinish:=True
    SolverFinish KeepFinal:=1

    Sheets("Edge5").Select
    SolverAdd CellRef:="$D$7", Relation:=1, FormulaText:="1000"
    SolverAdd CellRef:="$D$7", Relation:=3, FormulaText:="1+0.0000000001"
    SolverAdd CellRef:="$D$11", Relation:=1, FormulaText:="1.2"
    SolverOk SetCell:="$D$22", MaxMinVal:=2, ValueOf:=40, ByChange:="$D$7", Engine _
        :=1, EngineDesc:="GRG Nonlinear"
    SolverSolve (True)
    SolverSolve userFinish:=True
    SolverFinish KeepFinal:=1

    Sheets("Edge6").Select
    SolverAdd CellRef:="$D$7", Relation:=1, FormulaText:="1000"
    SolverAdd CellRef:="$D$7", Relation:=3, FormulaText:="1+0.0000000001"
    SolverAdd CellRef:="$D$11", Relation:=1, FormulaText:="1.2"
    SolverOk SetCell:="$D$22", MaxMinVal:=2, ValueOf:=40, ByChange:="$D$7", Engine _
        :=1, EngineDesc:="GRG Nonlinear"
    SolverSolve (True)
    SolverSolve userFinish:=True
    SolverFinish KeepFinal:=1
    
End Sub
