#!/usr/bin/env groovy

String tarquinBranch = "CPNA-1493"

library "tarquin@$tarquinBranch"

pipelinePy {
  pkgInfoPath = 'ignition/pkg_info.json'
  applicationName = 'ignition-framework'
  attachDocsToRelease = true
  releaseToPypi = true
}
