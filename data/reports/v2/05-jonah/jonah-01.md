# v1-he-baseline → v2-he-syntax: 05-jonah / jonah-01

## Summary

- v1-he-baseline lines: 122
- v2-he-syntax lines: 120
- Mechanical changes applied: 2
- REVIEW-REQUIRED items deferred to v4: 0

## Applied changes

### Change 1: line 17 → merge_with_next
- Validator: validate_line_final_tokens (rule L1.3b — stranded compound preposition)
- Severity: MALFORMED, Tag: STRONG-MERGE-CANDIDATE
- Brief: stranded compound preposition at line end: 'מִלִּפְנֵ֖י'
- Before:
  ```
  17: מִלִּפְנֵ֖י
  18: יְהוָֽה׃
  ```
- After:
  ```
  17: מִלִּפְנֵ֖י יְהוָֽה׃
  ```

### Change 2: line 14 → merge_with_next
- Validator: validate_line_final_tokens (rule L1.3b — stranded compound preposition)
- Severity: MALFORMED, Tag: STRONG-MERGE-CANDIDATE
- Brief: stranded compound preposition at line end: 'מִלִּפְנֵ֖י'
- Before:
  ```
  14: מִלִּפְנֵ֖י
  15: יְהוָ֑ה
  ```
- After:
  ```
  14: מִלִּפְנֵ֖י יְהוָ֑ה
  ```

## Deferred to v4 editorial review

_No items deferred._
