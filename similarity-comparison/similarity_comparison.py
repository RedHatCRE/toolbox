import configparser
import json
import re
import requests
import sqlite3
import subprocess
import sys
import xlsxwriter

from git import Repo
from os.path import expanduser
from sklearn.feature_extraction.text import TfidfVectorizer


httpRequest = {
    'requestJobsAndBuildInfo':
        "/api/json/?tree=jobs[name,lastBuild[result,number,timestamp]]",
    'requestJobs':
        "/api/json?tree=jobs[name]",
    'requestStableBuildArtifact':
        "/job/{jobName}/lastStableBuild/artifact/{artifactPath}",
    'requestArtifact':
        "/job/{jobName}/lastSuccessfulBuild/artifact/{artifactPath}"
}


def get_base_prefix_compat():
    """Get base/real prefix, or sys.prefix if there is none."""
    return getattr(sys, "base_prefix", None) or getattr(sys, "real_prefix",
                                                        None) or sys.prefix


def in_virtualenv():
    return get_base_prefix_compat() != sys.prefix


# JJSC - Jenkins Jobs Similarity Computation
class JJSC(object):
    def __init__(self, credentialsPath, artifactPath):
        configParser = configparser.RawConfigParser()
        print(configParser.read(credentialsPath))
        sectionName = "jenkins"
        dictionary = dict(configParser.items(sectionName))

        self.url = dictionary['url']
        self.artifactPath = artifactPath
        self.credentials = (dictionary['user'], dictionary['password'])

        # create (if !exists) a db to store <jobName, artifact>
        self.dbcon = sqlite3.connect('jjs.db')
        print("Connected to SQLite jjs.db")
        cursor = self.dbcon.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS jjs
                            ( jobName text,
                              artifatcContent text,
                              artifactCtntNrmlzd text )''')
        self.dbcon.commit()
        cursor.close()
        print("jjs table exists in jjs.db")

        self.workbook = xlsxwriter.Workbook('jjs.xlsx')

    def __del__(self):
        if self.dbcon:
            self.dbcon.close()
            print("The SQLite connection is closed")
        self.workbook.close()

    def _prepare_arg_parsing_and_serialization(self):
        # clone infrared
        git_url = "https://github.com/redhat-openstack/infrared.git"
        repo_dir = "/tmp/infrared"
        subprocess.call("rm -rf " + repo_dir, shell=True)
        Repo.clone_from(git_url, repo_dir)

        # apply the arg serialization patch
        command = "cp infrared_agrs_patch " + repo_dir + ";" + \
                  "cd " + repo_dir + ";" + \
                  "git apply infrared_agrs_patch"
        subprocess.call(command, shell=True)

        # install infarred in a virtual environment
        if (not in_virtualenv()):
            raise Exception("This code installs pip packages and is " +
                  "adviced to be executed in a virtual environment")

        command = "cd " + repo_dir + ";" + \
                  "pip install - U pip;" + \
                  "pip install ."
        subprocess.call(command, shell=True)

        # add additional plugins for enhanced parsing
        subprocess.call("infrared plugin add all", shell=True)

    def _insertDataIntoTable(self, jobName, artifatcContent):
        try:
            cursor = self.dbcon.cursor()
            sqlite_insert_with_param = """INSERT INTO jjs
                              (jobName, artifatcContent)
                              VALUES (?, ?);"""
            data_tuple = (jobName, artifatcContent)
            cursor.execute(sqlite_insert_with_param, data_tuple)
            self.dbcon.commit()
            cursor.close()
            return 0

        except sqlite3.Error as error:
            print("Failed to insert into sqlite table", error)
            return -1

    def populateDB(self):
        # get all Jobs
        request = requests.get(self.url + httpRequest['requestJobs'],
                               verify=False,
                               auth=self.credentials)
        jobsInJSON = json.loads(request.text)
        print(json.dumps(jobsInJSON, indent=4, sort_keys=True))

        skipList = ["util"]

        # get and store an artifact (if found)
        okCounter = 0
        insertCounter = 0
        for element in jobsInJSON['jobs']:
            print(element['name'])
            jobName = element['name']
            if jobName in skipList:
                continue
            requestStr = self.url + httpRequest['requestArtifact'].format(
                jobName=jobName,
                artifactPath=self.artifactPath)
            request = requests.get(requestStr, verify=False,
                                   auth=self.credentials)
            print(requestStr)
            if request.ok:
                okCounter = okCounter + 1
                if self._insertDataIntoTable(jobName, request.text) >= 0:
                    insertCounter = insertCounter + 1

        print("From populateDB")
        print("okCounter: " + str(okCounter))
        print("insertCounter: " + str(insertCounter))
        print("number of jobs: " + str(len(jobsInJSON['jobs'])))
        assert (okCounter == insertCounter)

    def _normilizeArtifact(self, artifact):
        regex = r".*infrared (tripleo-undercloud|tripleo-overcloud) .*\\*"
        plugin_names = "(tripleo-undercloud|tripleo-overcloud)"
        regex = r".*infrared " + plugin_names + " .*(([\r\n]*).*){4}"
        matches = re.finditer(regex, artifact, re.MULTILINE)
        normalizedArtifact = ""
        for matchNum, match in enumerate(matches, start=1):
            print(
                "Match {matchNum} was found at {start}-{end}: {match}".format(
                    matchNum=matchNum,
                    start=match.start(),
                    end=match.end(),
                    match=match.group()))
            normalizedArtifact = normalizedArtifact + "\n" + match.group()

        # TODO: filter out tempest invocation - DONE
        return (normalizedArtifact)

    def _extractVersionFromJobName(self, jobName):
        # matches XY.Z XY XY_Z in job names
        REGEXP = r'\s*([\d(.|_)]+)(_compact|-compact|_director|-director)\s*'

        version = re.search(REGEXP, jobName).group(1)
        version = version.replace("_", ".")  # for jobs with XY_Z

        return version

    def _extractIPVersionFromJobName(self, jobName):
        # matches XY.Z XY XY_Z in job names
        REGEXP = r".*ipv([\d]+).*"

        try:
            version = re.search(REGEXP, jobName).group(1)
        except AttributeError:
            version = "NA"

        return version

    # return true if artifact contains any of filter out criteria
    def _isFilteredOut(self, articact):
        filter = ["infrared tripleo-inventory",
                  "infrared workspace import",
                  "sshpass -p stack ssh -o UserKnownHostsFile=/dev/null",
                  "infrared tripleo-upgrade"]

        articactString = str(articact)

        intersestoin = [value for value in filter if value in articactString]

        return (len(intersestoin) > 0)

    def analyseJJSTable(self):
        cursor = self.dbcon.cursor()

        # fetch unified jobs
        sql_command = \
            'SELECT DISTINCT * FROM jjs WHERE jobName LIKE ' + \
            '\'%unified%\' AND jobName LIKE \'%director%\' ORDER BY jobName'
        cursor.execute(sql_command)
        unifiedJobs = cursor.fetchall()
        print("Total of unified jobs are:  ", len(unifiedJobs))

        # fetch other director jobs (including unified ones) to compare
        # against the unified jobs
        sql_command = \
            'SELECT DISTINCT * FROM jjs WHERE jobName LIKE ' + \
            '\'%director%\' AND jobName NOT LIKE \'%compact%\''
        cursor.execute(sql_command)
        directorJobs = cursor.fetchall()
        print("Total of director jobs are:  ", len(directorJobs))

        unifiedJobsCounter = 0
        cell_format = self.workbook.add_format(
            {'bold': True, 'font_color': 'red'})
        for rowUnified in unifiedJobs:
            jobNameUnified = str(rowUnified[0])
            print(len(unifiedJobs))
            try:
                unifiedJobsCounter += 1
                worksheet = self.workbook.add_worksheet(
                    jobNameUnified[1:28] + "--" + str(unifiedJobsCounter))
                worksheet.set_column(0, 0, len(jobNameUnified))
                worksheet.write(0, 0, jobNameUnified, cell_format)
                row = 1
            except xlsxwriter.exceptions.DuplicateWorksheetName:
                continue
            for rowDirector in directorJobs:
                jobNameDirector = str(rowDirector[0])
                releaseUnified = self._extractVersionFromJobName(
                    jobNameUnified)
                releaseDirector = self._extractVersionFromJobName(
                    jobNameDirector)
                ipVersionUnifed = self._extractIPVersionFromJobName(
                    jobNameUnified)
                ipVersionDirector = self._extractIPVersionFromJobName(
                    jobNameDirector)
                # if releaseUnified not in ["16.1", "16.2"]:
                #     continue

                if jobNameUnified != jobNameDirector and \
                        releaseUnified == releaseDirector and \
                        ipVersionUnifed == ipVersionDirector:
                    artifactUnified = str(rowUnified[1])
                    artifactDirector = str(rowDirector[1])
                    if self._isFilteredOut(artifactDirector):
                        continue
                    normalizedUnified = self._normilizeArtifact(
                        artifactUnified)
                    normalizedDirector = self._normilizeArtifact(
                        artifactDirector)
                    try:
                        tfidf = TfidfVectorizer().fit_transform(
                            [normalizedUnified, normalizedDirector])
                        # no need to normalize, since Vectorizer will return
                        # normalized tf-idf
                        pairwise_similarity = tfidf * tfidf.T
                    except Exception:
                        print("Can not compare " + rowUnified[0] + " and " +
                              rowDirector[0] + "\n")
                    threshold = pairwise_similarity.data.min()

                    if threshold >= 0.0:
                        wordsUnified = set(normalizedUnified.split())
                        wordsDirector = set(normalizedDirector.split())
                        unifiedUniques = set(
                            sorted(wordsUnified.difference(wordsDirector)))
                        directorUniques = set(
                            sorted(wordsDirector.difference(wordsUnified)))
                        uniques = unifiedUniques.union(directorUniques)
                        print(jobNameUnified + "," + str(unifiedUniques))
                        print(jobNameDirector + "," + str(directorUniques))
                        fstr = 'Total uniques: {}, Pairwise Similarity: {}\n'
                        print(fstr.format(len(uniques), threshold))
                        try:
                            worksheet.set_column(row, 0, len(jobNameDirector))
                            worksheet.write(row, 0, jobNameDirector)

                            threshold = round(threshold, 3)
                            worksheet.set_column(row, 1, len(str(threshold)))
                            worksheet.write(row, 1, str(threshold))

                            row = row + 1
                        except Exception as e:
                            print(e)
                            continue
        cursor.close()


credentialsPath = expanduser("~") + '/.config/jenkins_jobs/jenkins_jobs.ini'
artifactPath = '.sh/run.sh'
jjsc = JJSC(credentialsPath, artifactPath)

jjsc._prepare_arg_parsing_and_serialization()

jjsc.populateDB()
jjsc.analyseJJSTable()
del jjsc
