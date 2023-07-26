# Change Log

## [3.5.2](https://github.com/IBM/ignition/tree/3.5.2) (2023-07-26)
[Full Changelog](https://github.com/IBM/ignition/compare/3.5.1...3.5.2)


**Implemented enhancements:**

- python driver builds fails at docker step [\#172](https://github.com/IBM/ignition/issues/172)
  
## [3.5.1](https://github.com/IBM/ignition/tree/3.5.1) (2023-04-20)
[Full Changelog](https://github.com/IBM/ignition/compare/3.4.2...3.5.1)


**Implemented enhancements:**

- Change host to HOSTNAME in Driver logs[\#158](https://github.com/IBM/ignition/issues/158)
- Filter sensitive information on request/response body [\#161](https://github.com/IBM/ignition/issues/161)



## [3.4.2](https://github.com/IBM/ignition/tree/3.4.2) (2022-11-21)
[Full Changelog](https://github.com/IBM/ignition/compare/3.4.1...3.4.2)


**Implemented enhancements:**

- add error handling for sync calls   [\#152](https://github.com/IBM/ignition/issues/152)


## [3.4.1](https://github.com/IBM/ignition/tree/3.4.1) (2022-09-28)
[Full Changelog](https://github.com/IBM/ignition/compare/3.4.0...3.4.1)


**Implemented enhancements:**

- tenantId must be in camel case as per CP4NA standards for Python drivers [\#148](https://github.com/IBM/ignition/issues/148)


## [3.4.0](https://github.com/IBM/ignition/tree/3.4.0) (2022-09-05)
[Full Changelog](https://github.com/IBM/ignition/compare/3.3.1...3.4.0)


**Implemented enhancements:**

- Support Multi Tenancy for Lifecycle Drivers [\#137](https://github.com/IBM/ignition/issues/137)


## [3.3.1](https://github.com/IBM/ignition/tree/3.3.1) (2022-04-27)
[Full Changelog](https://github.com/IBM/ignition/compare/3.3.0...3.3.1)


**Fixed bugs:**

- Need to update Werkzeug 'BaseResponse' to 'Response' [\#130](https://github.com/IBM/ignition/issues/130)


## [3.3.0](https://github.com/IBM/ignition/tree/3.3.0) (2022-02-28)
[Full Changelog](https://github.com/IBM/ignition/compare/3.2.0...3.3.0)

**Removed Features:**

- Remove Swagger UI due to vulnerabilities [\#125](https://github.com/IBM/ignition/issues/125)

## [3.2.0](https://github.com/IBM/ignition/tree/3.2.0) (2021-12-10)
[Full Changelog](https://github.com/IBM/ignition/compare/3.1.0...3.2.0)

**Implemented enhancements:**

- Ensure Kafka messages are flushed on shutdown and the producer is closed [\#119](https://github.com/IBM/ignition/issues/119)

**Removed Features:**

- Remove uwsgi from driver template [\#116](https://github.com/IBM/ignition/issues/116)


## [3.1.0](https://github.com/IBM/ignition/tree/3.1.0) (2021-08-13)
[Full Changelog](https://github.com/IBM/ignition/compare/3.0.1...3.1.0)

**Implemented enhancements:**

- Uplift third party dependencies [\#111](https://github.com/IBM/ignition/issues/111)

**Fixed bugs:**

- None

## [3.0.1](https://github.com/IBM/ignition/tree/3.0.1) (2021-07-16)
[Full Changelog](https://github.com/IBM/ignition/compare/3.0.0...3.0.1)

**Implemented enhancements:**

- Uplift third party dependencies [\#104](https://github.com/IBM/ignition/issues/104)

**Fixed bugs:**

- Use tracectx instead of traceCtx in log fields [\#106](https://github.com/IBM/ignition/issues/106)

## [3.0.0](https://github.com/IBM/ignition/tree/3.0.0) (2021-04-29)
[Full Changelog](https://github.com/IBM/ignition/compare/2.0.4...3.0.0)

**Implemented enhancements:**

- Support Structured properties [\#100](https://github.com/IBM/ignition/issues/100)
- Add common services for logging the progress of a Resource lifecycle transition [\#99](https://github.com/IBM/ignition/issues/99)

## [2.0.4](https://github.com/IBM/ignition/tree/2.0.4) (2020-09-30)
[Full Changelog](https://github.com/IBM/ignition/compare/2.0.3...2.0.4)

**Implemented enhancements:**

- Expose Kafka Producer and Consumer Configuration [\#88](https://github.com/IBM/ignition/issues/88)
- Extend ResourceTemplateContextService to include associated topology [\#93](https://github.com/IBM/ignition/issues/93)
- Consistent NoBrokersAvailable exceptions on driver bootstrap in OCP Environments [\#97](https://github.com/IBM/ignition/issues/97)

## [2.0.3](https://github.com/IBM/ignition/tree/2.0.3) (2020-09-15)
[Full Changelog](https://github.com/IBM/ignition/compare/2.0.2...2.0.3)

**Implemented enhancements:**

- Increase default api_version_auto_timeout_ms value for topic creation [\#94](https://github.com/IBM/ignition/issues/94)

## [2.0.2](https://github.com/IBM/ignition/tree/2.0.2) (2020-06-10)
[Full Changelog](https://github.com/IBM/ignition/compare/2.0.1...2.0.2)

Re-release of broken 2.0.1

## [2.0.1](https://github.com/IBM/ignition/tree/2.0.1) (2020-06-09) (BROKEN)
[Full Changelog](https://github.com/IBM/ignition/compare/2.0.0...2.0.1)

**Fixed bugs:**
- NoBrokersAvailable exceptions during Kafka sends and receives [\#84](https://github.com/IBM/ignition/issues/84)

## [2.0.0](https://github.com/IBM/ignition/tree/2.0.0) (2020-05-19)
[Full Changelog](https://github.com/IBM/ignition/compare/1.1.0...2.0.0)

Works with ALM 2.2+

**Implemented enhancements:**
- Common Kubernetes deployment location [\#67](https://github.com/IBM/ignition/issues/67)
- Common templating tools [\#69](https://github.com/IBM/ignition/issues/69)
- Refactor render context builder keywords for system_properties, deployment_location and request_properties [\#72](https://github.com/IBM/ignition/issues/72)
- Refactor infrastructure and lifecycle APIs into single driver API [\#73](https://github.com/IBM/ignition/issues/73)
- Indicate syntax on templating capabiltiy [\#76](https://github.com/IBM/ignition/issues/73)
- Allow resource driver service to be notified when the lifecycle monitor has posted a response [\#78](https://github.com/IBM/ignition/issues/78)
- Templating services to support key properties [\#79](https://github.com/IBM/ignition/issues/79)
- Must include a notion of "removing" entries from Associated Topology [\#80](https://github.com/IBM/ignition/issues/80)
- Command utility to help with testing drivers [\#81](https://github.com/IBM/ignition/issues/81)

**Fixed bugs:**
- Request Queue max.poll.interval.ms is not configurable [\#75](https://github.com/IBM/ignition/issues/75)

**Documentation:**
- Docker image build instructions missing docker context path in command [\#65](https://github.com/IBM/ignition/issues/65)

Issues #67, #69, #72, #73, #75 and #76 were included in a 1.2.0 release but that release should have resulted in major version increase, so it is being phased out of this project's history. 

## [1.2.0](https://github.com/IBM/ignition/tree/1.1.0) (2020-05-12)
Do not use this release, use 2.0.0 instead.

## [1.1.0](https://github.com/IBM/ignition/tree/1.1.0) (2020-03-24)
[Full Changelog](https://github.com/IBM/ignition/compare/1.0.0...1.1.0)

**Fixed bugs:**
- Add support for a Request Queue [\#46](https://github.com/IBM/ignition/issues/46)

## [1.0.0](https://github.com/IBM/ignition/tree/1.0.0) (2020-02-20)
[Full Changelog](https://github.com/IBM/ignition/compare/0.9.0...1.0.0)

**Fixed bugs:**
- Private keys should not be logged [\#61](https://github.com/IBM/ignition/issues/61)

## [0.9.0](https://github.com/IBM/ignition/tree/0.9.0) (2020-02-12)
[Full Changelog](https://github.com/IBM/ignition/compare/0.8.0...0.9.0)

**Implemented enhancements:**
- LifecycleScripts workspace should be cleaned to save space on disk [\#58](https://github.com/IBM/ignition/issues/58)
- LifecycleScripts workspace should be auto-created [\#57](https://github.com/IBM/ignition/issues/57)

## [0.8.0](https://github.com/IBM/ignition/tree/0.8.0) (2020-01-27)
[Full Changelog](https://github.com/IBM/ignition/compare/0.7.0...0.8.0)

**Implemented enhancements:**
- Add autoscaling on CPU usage rules to template Helm charts [\#50](https://github.com/IBM/ignition/issues/50)
- Add health endpoint so drivers have an API to use for health checks in their pod deployments [\#53](https://github.com/IBM/ignition/issues/53)

**Fixed bugs:**
- KeyError: 'value' when iterating PropValueMap including an entry with no value [\#52](https://github.com/IBM/ignition/issues/52)

## [0.7.0](https://github.com/IBM/ignition/tree/0.7.0) (2020-01-13)
[Full Changelog](https://github.com/IBM/ignition/compare/0.6.2...0.7.0)

**Implemented enhancements:**
- Update infrastructure API to include systemProperties on create requests [\#48](https://github.com/IBM/ignition/issues/48)

## [0.6.2](https://github.com/IBM/ignition/tree/0.6.2) (2019-12-13)
[Full Changelog](https://github.com/IBM/ignition/compare/0.6.1...0.6.2)

**Fixed bugs:**
- PropValueMap does not allow values of None [\#44](https://github.com/IBM/ignition/issues/44)

## [0.6.1](https://github.com/IBM/ignition/tree/0.6.1) (2019-12-12)
[Full Changelog](https://github.com/IBM/ignition/compare/0.6.0...0.6.1)

**Fixed bugs:**
- PropValueMap items_with_types iterator has no termination check [\#42](https://github.com/IBM/ignition/issues/42)

## [0.6.0](https://github.com/IBM/ignition/tree/0.6.0) (2019-12-12)
[Full Changelog](https://github.com/IBM/ignition/compare/0.5.0...0.6.0)

**Fixed bugs:**

- UnicodeDecodeError: 'utf-8' codec can't decode byte 0x8f in position 5: invalid start byte [\#20](https://github.com/IBM/ignition/issues/20)
- Create command should not allow module names with dashes and special characters in module, helm and docker names [\#21](https://github.com/IBM/ignition/issues/21)
- Name used in setup.py of generated driver application should be the module name [\#27](https://github.com/IBM/ignition/issues/27)
- Correct driver template based on issues from other driver projects [\#28](https://github.com/IBM/ignition/issues/28)
- OpenAPI specification files are broken [\#37](https://github.com/IBM/ignition/issues/37)
- Logging Errors [\#29](https://github.com/IBM/ignition/issues/29)
- Job Queue thread aborts on error [\#31](https://github.com/IBM/ignition/issues/31)

**Implemented enhancements:**

- Validate app name [\#12](https://github.com/IBM/ignition/issues/12)
- Input properties should include property type [\#39](https://github.com/IBM/ignition/issues/39)
 
**Documentation:**

- Steps to build a docker image include incorrect whl directory [\#26](https://github.com/IBM/ignition/issues/26)
- Documentation should include details of how the framework should be used, preferaby with examples [\#25](https://github.com/IBM/ignition/issues/25)
- Document exception handling [\#18](https://github.com/IBM/ignition/issues/18)

## [0.5.0](https://github.com/IBM/ignition/tree/0.5.0) (2019-11-04)
[Full Changelog](https://github.com/IBM/ignition/compare/0.4.0...0.5.0)

**Implemented enhancements:**

- Add CLI with command to generate the necessary files to create a driver [\#17](https://github.com/IBM/ignition/issues/17)

## [0.4.0](https://github.com/IBM/ignition/tree/0.4.0) (2019-10-09)
[Full Changelog](https://github.com/IBM/ignition/compare/0.3.0...0.4.0)

**Fixed bugs:**

- Kafka consumer created without group id [\#14](https://github.com/IBM/ignition/issues/14)

**Implemented enhancements:**

- Configure Logstash-style logging that's compatible with LM/Filebeat logs [\#10](https://github.com/IBM/ignition/issues/10)

## [0.3.0](https://github.com/IBM/ignition/tree/0.3.0) (2019-10-01)
[Full Changelog](https://github.com/IBM/ignition/compare/0.2.0...0.3.0)

**Implemented enhancements:**

- Auto-create Kafka topics for Job queue [\#8](https://github.com/IBM/ignition/issues/8)
- Add templateType to infrastructure API [\#13](https://github.com/IBM/ignition/issues/13)

## [0.2.0](https://github.com/IBM/ignition/tree/0.2.0) (2019-09-18)
[Full Changelog](https://github.com/IBM/ignition/compare/0.1.0...0.2.0)

**Implemented enhancements:**

- Find API should not return 400 when nothing is found [\#6](https://github.com/IBM/ignition/issues/6)
- Not found response to return 400 code instead of 404 [\#4](https://github.com/IBM/ignition/issues/4)

**Fixed bugs:**

- Jobs not sent to Kafka queue when running in uwsgi  [\#2](https://github.com/IBM/ignition/issues/2)

**Merged pull requests:**

- Fixes \#6 by changing the Find Infrastructure API to return an empty result when no matching infrastructure is found [\#7](https://github.com/IBM/ignition/pull/7) ([dvaccarosenna](https://github.com/dvaccarosenna))
- issue4 - resolves issue \#4 to return a 400 status code when infrastru… [\#5](https://github.com/IBM/ignition/pull/5) ([dvaccarosenna](https://github.com/dvaccarosenna))
- issue2 - resolves \#2 by creating the producer when first needed [\#3](https://github.com/IBM/ignition/pull/3) ([dvaccarosenna](https://github.com/dvaccarosenna))

## [0.1.0](https://github.com/IBM/ignition/tree/0.1.0) (2019-09-02)
**Merged pull requests:**

- Develop [\#1](https://github.com/IBM/ignition/pull/1) ([dvaccarosenna](https://github.com/dvaccarosenna))



\* *This Change Log was automatically generated by [github_changelog_generator](https://github.com/skywinder/Github-Changelog-Generator)*
