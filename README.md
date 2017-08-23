### Workflow

* Condition: Script lookup for AMIs match `AMI_LOOKUP_PATTERN*`, continue...

* Condition: Script filters out AMIs older than `REMOVE_OLDER_THAN_X_DAYS` days, continue...

* Condition: Script force reserve `FORCE_KEEP_AMIS` AMIs

### Environment variable values

* `AMI_LOOKUP_PATTERN1`: `TEMPLATE_2016_Larry_*`

* `AMI_LOOKUP_PATTERN2`: `TEMPLATE_RedHat_Larry_*`

* `FORCE_KEEP_AMIS`: `3`

* `REMOVE_OLDER_THAN_X_DAYS`: `90`

### remove-old-amis.py

* Deploy in lambda

* Choose a role with sufficient privileges to run lambda

* Setup CloudWatch trigger to regularly run lambda
