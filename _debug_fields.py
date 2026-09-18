import json
from app.document_fields import extract_document_fields
from app.entity_extraction import extract_entities

text = r"""$\text{إسْمِ اللَّهُ الرَّحْمَٰنِ الرَّحِيمِ}$

# FEDERAL BOARD OF INTERMEDIATE AND SECONDARY EDUCATION
## ISLAMABAD

Serial No. 1512169  
Roll No. 1527311  
Group SCIENCE  

Certificate No. 282200100/164686  
Registration No. 2328220128  
Attempt(s) FIRST  

---

## SECONDARY SCHOOL CERTIFICATE EXAMINATION
### ANNUAL 2023

Certified that **NOOR FATIMA**  
Son / Daughter of **WAQAR AHMED**  
whose date of birth is 18-04-2007 (Eighteenth April, Two Thousand and Seven)  
has qualified for award of *Secondary School Certificate* as a Regular Candidate from  
**ARMY PUBLIC SCHOOL AND COLLEGE, SARGODHA CANTT.**

as per statement of marks given below and has obtained grade **A1**  
His / Her mark of identification : Nil

---

### SUBJECT-WISE STATEMENT OF MARKS

<table>
  <thead>
    <tr>
      <th>S.No.</th>
      <th>Subject(s)</th>
      <th colspan="2">MARKS</th>
    </tr>
    <tr>
      <th></th>
      <th></th>
      <th>Maximum</th>
      <th>Obtained</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>1</td><td>ENGLISH (COMPULSORY)</td><td>150</td><td>131</td></tr>
    <tr><td>2</td><td>URDU (COMPULSORY)</td><td>150</td><td>135</td></tr>
    <tr><td>3</td><td>ISLAMIYAT (COMPULSORY)</td><td>100</td><td>095</td></tr>
    <tr><td>4</td><td>PAKISTAN STUDIES</td><td>100</td><td>082</td></tr>
    <tr><td>5</td><td>MATHEMATICS</td><td>150</td><td>145</td></tr>
    <tr><td>6</td><td>PHYSICS</td><td>150</td><td>126</td></tr>
    <tr><td>7</td><td>CHEMISTRY</td><td>150</td><td>138</td></tr>
    <tr><td>8</td><td>BIOLOGY</td><td>150</td><td>132</td></tr>
    <tr><td></td><td>TOTAL</td><td>1100</td><td>984</td></tr>
  </tbody>
</table>

---

(Marks in words) **NINE HUNDRED EIGHTY-FOUR**

Islamabad Dated Feb 01, 2024"""

print(json.dumps(extract_document_fields(text), indent=2, ensure_ascii=False))
print(json.dumps(extract_entities(text), indent=2, ensure_ascii=False))
