#!/usr/bin/env python

from __future__ import print_function
import csv
import re
import argparse
import sys

class PollEverywhereStudent(object):
    def __init__(self, email, total_answered):
        self.email = email
        self.total_answered = int(total_answered)
        self.netid = self._get_netid(self.email.strip().lower())

    def __str__(self):
        return "%s: %d" % (self.netid, self.total_answers)

    @staticmethod
    def _get_netid(email):
        match = re.match(r"^([a-z]{2,3}[0-9]{1,5})@cornell\.edu$", email)
        if not match:
            raise ValueError("Cannot determine netid from email address: " + email)
        return match.groups()[0]

class CanvasStudent(object):
    def __init__(self, student, id, sis_user_id, sis_login_id, section):
        self.student=student
        self.id = id
        self.sis_user_id = sis_user_id
        self.sis_login_id = sis_login_id
        self.section = section

    def __str__(self):
        return "%s: %s" % (self.id, self.student)


def parse_canvas_gradebook(gradebook_file):
    students = {}
    print('Parsing canvas gradebook file: %s' % gradebook_file, file = sys.stderr)
    with open(gradebook_file, 'rb') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row['SIS Login ID']:
                print('  Skipping invalid row: %d' % reader.line_num, file=sys.stderr)
                continue
            students[row['SIS Login ID']]  = CanvasStudent(row['Student'],
                                    row['ID'],
                                    row['SIS User ID'],
                                    row['SIS Login ID'],
                                    row['Section'])
    return students


def parse_pollev_gradebook(pe_file):
    pollev_students = {}
    print('Parsing poll everywhere file: %s' % pe_file, file = sys.stderr)
    with open(pe_file, 'rb') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row['Email']:
                continue
            student = PollEverywhereStudent(row['Email'], row['Total answered'])
            pollev_students[student.netid] = student
    return pollev_students


def compare_students(canvas_student_netids, pollev_student_netids):
    """
    Look for issues with missing or malformed student ids or just students who didn't show up
    both arguments should be a list of strings
    """
    canvas_set = set(canvas_student_netids)
    pollev_set = set(pollev_student_netids)
    missing_pollev = sorted(list(canvas_set - pollev_set))
    if missing_pollev:
        print("The following students are in the canvas gradebook, but not in poll everywhere", file=sys.stderr)
        for student in missing_pollev:
            print("  %s" % student, file = sys.stderr)

    missing_canvas = sorted(list(pollev_set - canvas_set))
    if missing_canvas:
        print("The following students are in poll everywhere, but not in canvas", file=sys.stderr)
        for student in missing_canvas:
            print(" %s" % student, file = sys.stderr)

def output_result(canvas_students, pollev_students, activity_name, minimum_answered, output):
    writer = csv.writer(output)
    writer.writerow(['Student', 'ID', 'SIS User ID', 'SIS Login ID', 'Section', activity_name])
    for netid, student in canvas_students.iteritems():
        score = 0
        if netid in pollev_students:
             if pollev_students[netid].total_answered >= minimum_answered:
                score = 1
        writer.writerow([student.student, student.id, student.sis_user_id, student.sis_login_id, student.section, score])


def main(gradebook_file, pe_file, activity_name, minimum_answered, output_file=None):
    canvas_students = parse_canvas_gradebook(args.gradebook_file)
    pollev_students = parse_pollev_gradebook(args.pe_file)
    compare_students(canvas_students.keys(), pollev_students.keys())
    if output_file is not None:
        output = open(output_file, 'wb')
    else:
        output = sys.stdout
    output_result(canvas_students, pollev_students, activity_name, minimum_answered, output)
    if output_file is not None:
        output.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = "Combine Poll Everywhere results with a canvas gradebook",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("gradebook_file", help = "The gradebook file")
    parser.add_argument("pe_file", help = "The poll everywhere file")
    parser.add_argument("activity_name", help = "The name of the activity.  If there are spaces in the name, surround it with quotes")
    parser.add_argument("-n", "--minimum-answered", type = int, default = 1, help = "The minimum number of answered questions")
    parser.add_argument("-o", "--output-file", help = "The name of the file to which we should write.  Defaults to stdout.")
    args = parser.parse_args()


    main(args.gradebook_file, args.pe_file, args.activity_name, args.minimum_answered, args.output_file)
