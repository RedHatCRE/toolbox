# Copyright 2021 David Sariel
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import json
import re
import requests
import sqlite3
import xlsxwriter


from sklearn.feature_extraction.text import TfidfVectorizer
from os.path import expanduser

try:
    import configparser
except:
    from six.moves import configparser

httpRequest = { #'requestJobs': "/api/json/?tree=jobs[name,lastBuild[result,number,timestamp]]",
               'requestJobs': "/api/json?tree=jobs[name]",
               #'requestArtifact': "/job/{jobName}/lastStableBuild/artifact/{artifactPath}",
               'requestArtifact': "/job/{jobName}/lastSuccessfulBuild/artifact/{artifactPath}"
              }



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
                       (jobName text, artifatcContent text, artifactCtntNrmlzd text)''')
        self.dbcon.commit()
        cursor.close()
        print("jjs table exists in jjs.db")

        self.workbook = xlsxwriter.Workbook('jjs.xlsx')

    def __del__(self):
        if self.dbcon:
            self.dbcon.close()
            print("The SQLite connection is closed")
        self.workbook.close()


    def _insertDataIntoTable(self, jobName,  artifatcContent):
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
                               auth=credentials)
        jobsInJSON = json.loads(request.text)
        print(json.dumps(jobsInJSON, indent=4, sort_keys=True))

        skipList = ["util"]

        # get and store an artifact (if found)
        okCounter = 0
        insertCounter = 0
        for element in jobsInJSON['jobs']:
            print (element['name'])
            jobName = element['name']
            if jobName in skipList:
                continue
            requestStr = self.url + httpRequest['requestArtifact'].format(jobName = jobName,
                                                                          artifactPath = self.artifactPath)
            request = requests.get(requestStr, verify=False, auth=credentials)
            print(requestStr)
            if request.ok:
                okCounter = okCounter + 1
                if self._insertDataIntoTable(jobName,request.text) >= 0:
                    insertCounter = insertCounter + 1

        print("From populateDB")
        print("okCounter: " + str(okCounter))
        print("insertCounter: " + str(insertCounter))
        print("number of jobs: " + str(len(jobsInJSON['jobs'])))
        assert (okCounter == insertCounter)


    def _normilizeArtifact(self, artifact):
        regex = r".*infrared (tripleo-undercloud|tripleo-overcloud) .*\\*"
        regex = r".*infrared (tripleo-undercloud|tripleo-overcloud) .*(([\r\n]*).*){4}"
        matches = re.finditer(regex, artifact, re.MULTILINE)
        normalizedArtifact = ""
        for matchNum, match in enumerate(matches, start=1):
            # print("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum=matchNum,
            #                                                                     start=match.start(),
            #                                                                     end=match.end(),
            #                                                                     match=match.group()))
            normalizedArtifact = normalizedArtifact + "\n" + match.group()

        #TODO: filter out tempest invocation - DONE
        return (normalizedArtifact)


    def _extractVersionFromJobName(self, jobName):
        # matches XY.Z XY XY_Z in job names
        REGEXP = r'\s*([\d(.|_)]+)(_compact|-compact|_director|-director)\s*'

        version = re.search(REGEXP, jobName).group(1)
        version = version.replace("_", ".") # for jobs with XY_Z

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
        cursor.execute('SELECT DISTINCT * FROM jjs WHERE jobName LIKE \'%unified%\' AND jobName LIKE \'%director%\' ORDER BY jobName')
        unifiedJobs = cursor.fetchall()
        print("Total of unified jobs are:  ", len(unifiedJobs))

        # fetch other director jobs (including unified ones) to compare against the unified jobs
        cursor.execute('SELECT DISTINCT * FROM jjs WHERE jobName LIKE \'%director%\' AND jobName NOT LIKE \'%compact%\'')
        directorJobs = cursor.fetchall()
        print("Total of director jobs are:  ", len(directorJobs))

        unifiedJobsCounter = 0
        cell_format = self.workbook.add_format({'bold': True, 'font_color': 'red'})
        for rowUnified in unifiedJobs:
            jobNameUnified = str(rowUnified[0])
            print (len(unifiedJobs))
            try:
                unifiedJobsCounter += 1
                worksheet = self.workbook.add_worksheet(jobNameUnified[1:28]+"--" +str(unifiedJobsCounter))
                worksheet.set_column(0, 0, len(jobNameUnified))
                worksheet.write(0, 0, jobNameUnified, cell_format)
                row = 1
            except xlsxwriter.exceptions.DuplicateWorksheetName:
                continue
            for rowDirector in directorJobs:
                jobNameDirector = str(rowDirector[0])
                releaseUnified = self._extractVersionFromJobName(jobNameUnified)
                releaseDirector = self._extractVersionFromJobName(jobNameDirector)
                ipVersionUnifed = self._extractIPVersionFromJobName(jobNameUnified)
                ipVersionDirector  = self._extractIPVersionFromJobName(jobNameDirector)
                # if releaseUnified not in ["16.1", "16.2"]:
                #     continue

                if jobNameUnified != jobNameDirector and \
                   releaseUnified == releaseDirector and \
                   ipVersionUnifed == ipVersionDirector:
                    artifactUnified = str(rowUnified[1])
                    artifactDirector = str(rowDirector[1])
                    if self._isFilteredOut(artifactDirector):
                        continue
                    normalizedUnified = self._normilizeArtifact(artifactUnified)
                    normalizedDirector = self._normilizeArtifact(artifactDirector)
                    try:
                        tfidf = TfidfVectorizer().fit_transform([normalizedUnified, normalizedDirector])
                        # no need to normalize, since Vectorizer will return normalized tf-idf
                        pairwise_similarity = tfidf * tfidf.T
                    except Exception as e:
                        print("Can not compare " + rowUnified[0] + " and " + rowDirector[0] + "\n")
                    threshold = pairwise_similarity.data.min()

                    if threshold >= 0.0:
                        # print(rowUnified[0] + " and " + rowDirector[0] + " are " + str(threshold) + " similar")
                        wordsUnified = set(normalizedUnified.split())
                        wordsDirector = set(normalizedDirector.split())
                        unifiedUniques = set(sorted(wordsUnified.difference(wordsDirector)))
                        directorUniques = set(sorted(wordsDirector.difference(wordsUnified)))
                        uniques = unifiedUniques.union(directorUniques)
                        #print(jobNameUnified + "," + jobNameDirector + "," + str(threshold))
                        print(jobNameUnified+ "," + str(unifiedUniques))
                        print(jobNameDirector+ "," + str(directorUniques))
                        print('Total uniques: {}, Pairwise Similarity: {}\n\n'.format(len(uniques), threshold))
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
#jjsc.populateDB()
jjsc.analyseJJSTable()
del jjsc
