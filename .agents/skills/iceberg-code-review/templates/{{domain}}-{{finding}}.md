---
title: '{{domain}}-{{finding}}'
description: '{{description}}'    # write simply
type: 'code-review-finding'
severity: '{{severity}}'
status: '{{status}}'
---

<!--
Code review finding report template.
-->
- Location: [{{location}}](/{{location_link}})

## Summary

<!-- Write Summary -->

## Observation

<!-- Write Observation (Pick one format below, remove others) -->
- **{{focus}} {{core}}**: {{observation}}
  {{additional_text}}
- **{{focus}} {{core}}**: {{observation}}
  - {{additional_bullet_1}}
  - {{additional_bullet_2}}

## Impact

<!-- Write Impact (Pick one format below, remove others) -->
- **{{focus}} {{core}}**: {{impact}}
  {{additional_text}}
- **{{focus}} {{core}}**: {{impact}}
  - {{additional_bullet_1}}
  - {{additional_bullet_2}}

## Recommendation

<!-- Write Recommendation (Pick one format below, remove others) -->
- **{{action}} {{what}}**: {{recommendation}}
  {{additional_text}}
- **{{action}} {{what}}**: {{recommendation}}
  - {{additional_bullet_1}}
  - {{additional_bullet_2}}

## Verification

<!-- Write Verification (Pick one format below, remove others) -->
- **{{action}} {{what}}**: {{verification}}
  {{additional_text}}
- **{{action}} {{what}}**: {{verification}}
  - {{additional_bullet_1}}
  - {{additional_bullet_2}}
