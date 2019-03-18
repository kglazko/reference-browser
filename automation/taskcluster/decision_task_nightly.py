# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Decision task for nightly releases.
"""

from __future__ import print_function

import argparse
import arrow
import json
import lib.tasks
import os
import taskcluster

TASK_ID = os.environ.get('TASK_ID')
SCHEDULER_ID = os.environ.get('SCHEDULER_ID')
GITHUB_HTTP_REPOSITORY = os.environ.get('MOBILE_HEAD_REPOSITORY')
HEAD_REV = os.environ.get('MOBILE_HEAD_REV')

BUILDER = lib.tasks.TaskBuilder(
    task_id=TASK_ID,
    owner="kglazko@mozilla.com",
    source='{}/raw/{}/.taskcluster.yml'.format(GITHUB_HTTP_REPOSITORY, HEAD_REV),
    scheduler_id=SCHEDULER_ID,
    build_worker_type=os.environ.get('BUILD_WORKER_TYPE'),
)


def generate_build_task():
    return taskcluster.slugId(), BUILDER.build_task(
        name="(Reference Browser) Build task",
        description="Build Reference Browser from source code.",
        command=('echo "--" > .adjust_token'
                 #' && python automation/taskcluster/helper/get-secret.py'
                 ' && ./gradlew --no-daemon -PcrashReportEnabled=true -Ptelemetry=true clean assembleDebug'),
        scopes=[
        ]
    )

def generate_unit_test_task(build_task_id):
    return taskcluster.slugId(), BUILDER.craft_unit_test_task(
        build_task_id,
        name="(RB) Unit tests",
        description="Run unit tests for RB for Android.",
        command='echo "--" > .adjust_token && ./gradlew --no-daemon clean test',
        dependencies=[build_task_id]
    )

# For GeckoView, upload nightly (it has release config) by default, all Release builds have WV
def generate_upload_apk_nimbledroid_task(build_task_id):
    return taskcluster.slugId(), BUILDER.craft_upload_apk_nimbledroid_task(
        build_task_id,
        name="(RB for Android) Upload Debug APK to Nimbledroid",
        description="Upload APKs to Nimbledroid for performance measurement and tracking.",
        command=('echo "--" > .adjust_token'
                 ' && cd ..'
                 '&& git clone %s'
                 ' && cd reference-browser'
                 ' && python automation/taskcluster/upload_apk_nimbledroid.py'),
        dependencies= [build_task_id],
        scopes=[],
)


def populate_chain_of_trust_required_but_unused_files():
    # These files are needed to keep chainOfTrust happy. However, they have no need for Reference Browser
    # at the moment. For more details, see: https://github.com/mozilla-releng/scriptworker/pull/209/files#r184180585

    for file_name in ('actions.json', 'parameters.yml'):
        with open(file_name, 'w') as f:
            json.dump({}, f)


def nightly():
    queue = taskcluster.Queue({'baseUrl': 'http://taskcluster/queue/v1'})

    task_graph = {}

    build_task_id, build_task = generate_build_task()
    lib.tasks.schedule_task(queue, build_task_id, build_task)

    task_graph[build_task_id] = {}
    task_graph[build_task_id]['task'] = queue.task(build_task_id)

    #unit_test_task_id, unit_test_task = generate_unit_test_task(build_task_id)
    #lib.tasks.schedule_task(queue, unit_test_task_id, unit_test_task)

    #task_graph[unit_test_task_id] = {}
    #task_graph[unit_test_task_id]['task'] = queue.task(unit_test_task_id)

    upload_nd_task_id, upload_nd_task = generate_upload_apk_nimbledroid_task(build_task_id)
    lib.tasks.schedule_task(queue, upload_nd_task_id, upload_nd_task)

    task_graph[upload_nd_task_id] = {}
    task_graph[upload_nd_task_id]['task'] = queue.task(upload_nd_task_id)

    print(json.dumps(task_graph, indent=4, separators=(',', ': ')))

    with open('task-graph.json', 'w') as f:
        json.dump(task_graph, f)

    populate_chain_of_trust_required_but_unused_files()


if __name__ == "__main__":
    nightly()
