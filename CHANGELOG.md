# Change Log

## [0.9.0](https://github.com/accanto-systems/ignition/tree/0.9.0) (2020-02-12)
[Full Changelog](https://github.com/accanto-systems/ignition/compare/0.8.0...0.9.0)

**Implemented enhancements:**
- LifecycleScripts workspace should be cleaned to save space on disk [\#58](https://github.com/accanto-systems/ignition/issues/58)
- LifecycleScripts workspace should be auto-created [\#57](https://github.com/accanto-systems/ignition/issues/57)

## [0.8.0](https://github.com/accanto-systems/ignition/tree/0.8.0) (2020-01-27)
[Full Changelog](https://github.com/accanto-systems/ignition/compare/0.7.0...0.8.0)

**Implemented enhancements:**
- Add autoscaling on CPU usage rules to template Helm charts [\#50](https://github.com/accanto-systems/ignition/issues/50)
- Add health endpoint so drivers have an API to use for health checks in their pod deployments [\#53](https://github.com/accanto-systems/ignition/issues/53)

**Fixed bugs:**
- KeyError: 'value' when iterating PropValueMap including an entry with no value [\#52](https://github.com/accanto-systems/ignition/issues/52)

## [0.7.0](https://github.com/accanto-systems/ignition/tree/0.7.0) (2020-01-13)
[Full Changelog](https://github.com/accanto-systems/ignition/compare/0.6.2...0.7.0)

**Implemented enhancements:**
- Update infrastructure API to include systemProperties on create requests [\#48](https://github.com/accanto-systems/ignition/issues/48)

## [0.6.2](https://github.com/accanto-systems/ignition/tree/0.6.2) (2019-12-13)
[Full Changelog](https://github.com/accanto-systems/ignition/compare/0.6.1...0.6.2)

**Fixed bugs:**
- PropValueMap does not allow values of None [\#44](https://github.com/accanto-systems/ignition/issues/44)

## [0.6.1](https://github.com/accanto-systems/ignition/tree/0.6.1) (2019-12-12)
[Full Changelog](https://github.com/accanto-systems/ignition/compare/0.6.0...0.6.1)

**Fixed bugs:**
- PropValueMap items_with_types iterator has no termination check [\#42](https://github.com/accanto-systems/ignition/issues/42)

## [0.6.0](https://github.com/accanto-systems/ignition/tree/0.6.0) (2019-12-12)
[Full Changelog](https://github.com/accanto-systems/ignition/compare/0.5.0...0.6.0)

**Fixed bugs:**

- UnicodeDecodeError: 'utf-8' codec can't decode byte 0x8f in position 5: invalid start byte [\#20](https://github.com/accanto-systems/ignition/issues/20)
- Create command should not allow module names with dashes and special characters in module, helm and docker names [\#21](https://github.com/accanto-systems/ignition/issues/21)
- Name used in setup.py of generated driver application should be the module name [\#27](https://github.com/accanto-systems/ignition/issues/27)
- Correct driver template based on issues from other driver projects [\#28](https://github.com/accanto-systems/ignition/issues/28)
- OpenAPI specification files are broken [\#37](https://github.com/accanto-systems/ignition/issues/37)
- Logging Errors [\#29](https://github.com/accanto-systems/ignition/issues/29)
- Job Queue thread aborts on error [\#31](https://github.com/accanto-systems/ignition/issues/31)

**Implemented enhancements:**

- Validate app name [\#12](https://github.com/accanto-systems/ignition/issues/12)
- Input properties should include property type [\#39](https://github.com/accanto-systems/ignition/issues/39)
 
**Documentation:**

- Steps to build a docker image include incorrect whl directory [\#26](https://github.com/accanto-systems/ignition/issues/26)
- Documentation should include details of how the framework should be used, preferaby with examples [\#25](https://github.com/accanto-systems/ignition/issues/25)
- Document exception handling [\#18](https://github.com/accanto-systems/ignition/issues/18)

## [0.5.0](https://github.com/accanto-systems/ignition/tree/0.5.0) (2019-11-04)
[Full Changelog](https://github.com/accanto-systems/ignition/compare/0.4.0...0.5.0)

**Implemented enhancements:**

- Add CLI with command to generate the necessary files to create a driver [\#17](https://github.com/accanto-systems/ignition/issues/17)

## [0.4.0](https://github.com/accanto-systems/ignition/tree/0.4.0) (2019-10-09)
[Full Changelog](https://github.com/accanto-systems/ignition/compare/0.3.0...0.4.0)

**Fixed bugs:**

- Kafka consumer created without group id [\#14](https://github.com/accanto-systems/ignition/issues/14)

**Implemented enhancements:**

- Configure Logstash-style logging that's compatible with LM/Filebeat logs [\#10](https://github.com/accanto-systems/ignition/issues/10)

## [0.3.0](https://github.com/accanto-systems/ignition/tree/0.3.0) (2019-10-01)
[Full Changelog](https://github.com/accanto-systems/ignition/compare/0.2.0...0.3.0)

**Implemented enhancements:**

- Auto-create Kafka topics for Job queue [\#8](https://github.com/accanto-systems/ignition/issues/8)
- Add templateType to infrastructure API [\#13](https://github.com/accanto-systems/ignition/issues/13)

## [0.2.0](https://github.com/accanto-systems/ignition/tree/0.2.0) (2019-09-18)
[Full Changelog](https://github.com/accanto-systems/ignition/compare/0.1.0...0.2.0)

**Implemented enhancements:**

- Find API should not return 400 when nothing is found [\#6](https://github.com/accanto-systems/ignition/issues/6)
- Not found response to return 400 code instead of 404 [\#4](https://github.com/accanto-systems/ignition/issues/4)

**Fixed bugs:**

- Jobs not sent to Kafka queue when running in uwsgi  [\#2](https://github.com/accanto-systems/ignition/issues/2)

**Merged pull requests:**

- Fixes \#6 by changing the Find Infrastructure API to return an empty result when no matching infrastructure is found [\#7](https://github.com/accanto-systems/ignition/pull/7) ([dvaccarosenna](https://github.com/dvaccarosenna))
- issue4 - resolves issue \#4 to return a 400 status code when infrastru… [\#5](https://github.com/accanto-systems/ignition/pull/5) ([dvaccarosenna](https://github.com/dvaccarosenna))
- issue2 - resolves \#2 by creating the producer when first needed [\#3](https://github.com/accanto-systems/ignition/pull/3) ([dvaccarosenna](https://github.com/dvaccarosenna))

## [0.1.0](https://github.com/accanto-systems/ignition/tree/0.1.0) (2019-09-02)
**Merged pull requests:**

- Develop [\#1](https://github.com/accanto-systems/ignition/pull/1) ([dvaccarosenna](https://github.com/dvaccarosenna))



\* *This Change Log was automatically generated by [github_changelog_generator](https://github.com/skywinder/Github-Changelog-Generator)*