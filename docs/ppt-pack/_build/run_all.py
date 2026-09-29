"""Render the six Saathi diagrams: page 1 sized to the drawing, page 2 = redraw spec + Mermaid source."""
import diagrams as D
import render as R

for fname, title, subtitle, direction, groups, edges, classes, dashed in D.DIAGRAMS:
    code = D.flowchart(direction, groups, edges, classes=classes, dashed=dashed)
    R.build(fname, title, subtitle, code, D.spec(groups, edges), elk=True)
