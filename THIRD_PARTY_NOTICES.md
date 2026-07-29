# Third-party content and notices

The MIT License in this repository applies only to original source code and
documentation contributed to this repository.

It does **not** grant any rights to dictionary entries, definitions, examples,
illustrations, audio, fonts, branding, or other content extracted from third-party
dictionary products. Those materials remain subject to the terms of their respective
rightsholders and are intentionally excluded from the Git repository.

The current converters have been tested with locally owned copies of:

- Oxford Advanced Learner's Dictionary data;
- 《新世纪日汉双解大辞典》;
- 《新日汉拟声拟态词词典》.

Naming a product describes compatibility only and does not imply endorsement or
affiliation. Public download availability is a technical distribution state and must
not be read as a claim that the repository owns the underlying dictionary content.

Before adding or replacing a public generated dictionary, verify all of the following
where applicable:

1. the source and edition are identified accurately;
2. known license, attribution, and share-alike terms are preserved;
3. definitions, examples, images, audio, and fonts are considered separately;
4. no permission, license, or publisher affiliation is asserted without evidence;
5. personal data, credentials, local paths, and proprietary source files are absent
   from the Git repository.

Dependencies retain their own licenses. In particular, the build pipeline uses
`yomichan-dict-builder`, `mdict-utils`, `lxml`, and `fastjsonschema`.
