# MedBot CLI Test Results - High Confidence Questions

**Test Date:** 2026-02-06
**Total Questions Tested:** 27
**High Confidence (>=75%):** 20
**Medium Confidence (55-74%):** 7
**Low Confidence (<55%):** 0

---

## Summary

| # | Question | Category | Confidence | Fallback |
|---|----------|----------|------------|----------|
| 1 | What are the symptoms and treatment options for Non-Small Cell Lung Cancer? | symptoms | 100% | No |
| 2 | What are the common side effects of ibuprofen? | medication | 93% | No |
| 3 | What is Type 2 Diabetes and how is it managed? | symptoms | 90% | No |
| 4 | What are the risk factors and early signs of breast cancer? | symptoms | 98% | No |
| 5 | What is the recommended treatment for hypertension? | symptoms | 77% | No |
| 6 | What are the warning signs of a stroke? | symptoms | 84% | No |
| 7 | What are the uses and warnings for acetaminophen? | medication | 82% | No |
| 8 | What is Alzheimer's disease and what are its stages? | symptoms | 100% | No |
| 9 | What are the symptoms and causes of chronic kidney disease? | symptoms | 100% | No |
| 10 | What is the mechanism of action of metformin in treating diabetes? | medication | 77% | Yes (mixed) |
| 11 | What are the diagnostic criteria for rheumatoid arthritis? | symptoms | 74% | No |
| 12 | What is the pathophysiology of asthma and what triggers exacerbations? | symptoms | 91% | No |
| 13 | What are the side effects and drug interactions of aspirin? | medication | 75% | No |
| 14 | What is the differential diagnosis for chest pain? | symptoms | 82% | No |
| 15 | What are the clinical manifestations of Parkinson's disease? | symptoms | 100% | No |
| 16 | What are the complications of untreated hyperthyroidism? | symptoms | 76% | No |
| 17 | What is the first-line treatment for community-acquired pneumonia? | symptoms | 77% | No |
| 18 | What are the contraindications for using warfarin? | symptoms | 66% | No |
| 19 | What are the symptoms and treatment of epilepsy? | symptoms | 100% | No |
| 20 | What is the prognosis and survival rate for pancreatic cancer? | symptoms | 69% | No |
| 21 | What are the indications and side effects of omeprazole? | medication | 65% | No |
| 22 | What are the stages and treatment of colorectal cancer? | symptoms | 77% | No |
| 23 | What are the symptoms of myocardial infarction and how is it treated emergently? | symptoms | 74% | No |
| 24 | What are the clinical features and management of multiple sclerosis? | symptoms | 92% | No |
| 25 | What is the recommended dosage and precautions for amoxicillin? | medication | 66% | No |
| 26 | What are the causes and management of iron deficiency anemia? | symptoms | 100% | No |
| 27 | What are the symptoms and treatment of celiac disease? | symptoms | 100% | No |

---

## High Confidence Questions (>=75%)

These questions consistently returned high-quality, well-sourced answers from the RAG system.

### 100% Confidence (Perfect Match)

| # | Question | Category |
|---|----------|----------|
| 1 | What are the symptoms and treatment options for Non-Small Cell Lung Cancer? | symptoms |
| 8 | What is Alzheimer's disease and what are its stages? | symptoms |
| 9 | What are the symptoms and causes of chronic kidney disease? | symptoms |
| 15 | What are the clinical manifestations of Parkinson's disease? | symptoms |
| 19 | What are the symptoms and treatment of epilepsy? | symptoms |
| 26 | What are the causes and management of iron deficiency anemia? | symptoms |
| 27 | What are the symptoms and treatment of celiac disease? | symptoms |

### 90-99% Confidence

| # | Question | Category | Confidence |
|---|----------|----------|------------|
| 2 | What are the common side effects of ibuprofen? | medication | 93% |
| 3 | What is Type 2 Diabetes and how is it managed? | symptoms | 90% |
| 4 | What are the risk factors and early signs of breast cancer? | symptoms | 98% |
| 12 | What is the pathophysiology of asthma and what triggers exacerbations? | symptoms | 91% |
| 24 | What are the clinical features and management of multiple sclerosis? | symptoms | 92% |

### 75-89% Confidence

| # | Question | Category | Confidence |
|---|----------|----------|------------|
| 5 | What is the recommended treatment for hypertension? | symptoms | 77% |
| 6 | What are the warning signs of a stroke? | symptoms | 84% |
| 7 | What are the uses and warnings for acetaminophen? | medication | 82% |
| 10 | What is the mechanism of action of metformin in treating diabetes? | medication | 77% |
| 13 | What are the side effects and drug interactions of aspirin? | medication | 75% |
| 14 | What is the differential diagnosis for chest pain? | symptoms | 82% |
| 16 | What are the complications of untreated hyperthyroidism? | symptoms | 76% |
| 17 | What is the first-line treatment for community-acquired pneumonia? | symptoms | 77% |
| 22 | What are the stages and treatment of colorectal cancer? | symptoms | 77% |

---

## Medium Confidence Questions (55-74%)

These questions returned reasonable answers but with lower retrieval confidence. The system flagged them with warnings.

| # | Question | Category | Confidence | Notes |
|---|----------|----------|------------|-------|
| 11 | What are the diagnostic criteria for rheumatoid arthritis? | symptoms | 74% | Medium confidence warning shown |
| 18 | What are the contraindications for using warfarin? | symptoms | 66% | Medium confidence warning; detected as symptoms instead of medication |
| 20 | What is the prognosis and survival rate for pancreatic cancer? | symptoms | 69% | Medium confidence warning |
| 21 | What are the indications and side effects of omeprazole? | medication | 65% | Medium confidence warning |
| 23 | What are the symptoms of myocardial infarction and how is it treated emergently? | symptoms | 74% | Medium confidence warning |
| 25 | What is the recommended dosage and precautions for amoxicillin? | medication | 66% | Medium confidence warning |

---

## Observations

### Strengths
1. **Disease-specific symptom queries perform best** - Questions about well-known conditions (NSCLC, Alzheimer's, Parkinson's, epilepsy, celiac disease, CKD, iron deficiency anemia) consistently hit 100% confidence.
2. **Common OTC medication queries are strong** - Ibuprofen (93%) and acetaminophen (82%) are well-represented in the FDA database.
3. **Cancer-related queries** generally perform well, especially for common cancers with detailed MedQuAD entries.
4. **Asthma and MS** showed excellent retrieval (91% and 92%), suggesting good coverage of chronic conditions.

### Areas for Improvement
1. **Prescription medication queries** tend to get lower confidence (warfarin 66%, omeprazole 65%, amoxicillin 66%) - the FDA drug label database may have less detailed clinical information for these.
2. **Highly specific clinical questions** (diagnostic criteria, contraindications, prognosis/survival rates) tend to get medium confidence, suggesting the knowledge base is better at general condition overviews than specialized clinical details.
3. **Intent detection quirk** - Some medication-related questions (e.g., warfarin contraindications) are detected as "symptoms" rather than "medication", which may route them to the wrong collection.
4. **Metformin** required a fallback to the mixed collection (77%), indicating the primary medication database may not cover mechanism-of-action details well.

### Recommended Test Questions for Demos (All >=90%)
```
What are the symptoms and treatment options for Non-Small Cell Lung Cancer?
What are the common side effects of ibuprofen?
What is Type 2 Diabetes and how is it managed?
What are the risk factors and early signs of breast cancer?
What is Alzheimer's disease and what are its stages?
What are the symptoms and causes of chronic kidney disease?
What are the clinical manifestations of Parkinson's disease?
What is the pathophysiology of asthma and what triggers exacerbations?
What are the symptoms and treatment of epilepsy?
What are the causes and management of iron deficiency anemia?
What are the symptoms and treatment of celiac disease?
What are the clinical features and management of multiple sclerosis?
```
