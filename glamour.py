from __future__ import print_function
import sys, shutil, urllib2, os, plistlib, getpass, time, datetime #vanilla python libraries

#Dependencies
from git import *
import yaml
import paramiko


script_directory = os.path.dirname(os.path.realpath(__file__))
working_directory = os.path.dirname(os.path.realpath(__file__)) + "/tmp"
glamour_settings = yaml.load(file(script_directory+"/glamour_config.yml"))


class glamour:

    def __init__(self):
        self.sftp_password = glamour_settings["sftp_password"] #hardcode

    def release(self, make_clean = True):
        self.clean_local()
        os.mkdir(working_directory)
        self.check_for_release_issues()
        

        
        print("Publishing " + glamour_settings["app_name"] + " release " + str(self.get_current_app_version()))
        
        
        
        self.write_appcast_and_upload_to_sftp()
        
        self.write_release_notes_and_upload_to_sftp()

        self.write_release_log_and_upload_to_sftp()

        self.zip_app_and_upload_to_sftp()
        


        #clean up those temp files
        if make_clean:
            print("Cleaning up temp files... ", end = '')
            self.clean_local()
            print("Done cleaning")

    def check_for_release_issues(self):
        issues = ""
        current_version_hash = self.get_version_hash_from_version_number(str(self.get_current_app_version()))
        previous_version_hash = self.get_version_hash_from_version_number(str(self.get_current_app_version()-1))

        try:
            versions_data = yaml.load(urllib2.urlopen(self.get_https_url("releases.yml")))
        except urllib2.HTTPError:
            return ""

        issue_exists = False

        try:
            if versions_data[str(self.get_current_app_version())] is not None:
                print("You are about to overwrite an existing update.")
                issue_exists = True
        except KeyError:
            pass

        if previous_version_hash is not None:
            if current_version_hash["head"] == previous_version_hash["head"]:
                print("You have not git commited since the previous version - your changelog will be innaccurate.")
                issue_exists = True

        if issue_exists:
            if raw_input("Are you sure you want to continue? (y/n) ").lower()[0] == "n":
                self.clean_local()
                sys.exit(0)
        

    def clean_local(self):
        if os.path.exists(working_directory):
            shutil.rmtree(working_directory)

    def write_release_log_and_upload_to_sftp(self):
        versions_data = self.get_versions_data()
        release_log_temp_file = open(self.get_working_path("releases.yml"), 'w')
        
        release_log_temp_file.write(yaml.dump(yaml.load(str(versions_data)), default_flow_style=False))
        release_log_temp_file.close()
        self.save_file_to_sftp_appcast_directory(self.get_working_path("releases.yml"))

    def write_release_notes_and_upload_to_sftp(self):
        versions_data = self.get_versions_data()
        release_notes_temp_file = open(self.get_working_path("release_notes.html"), 'w')

        release_notes_template_file = open(self.get_support_files_path("release_notes.template.html"), 'rU')
        release_notes_template_data = ""
        for line in release_notes_template_file.readlines():
            release_notes_template_data += line


        
        release_notes_versions_data = ""
        for version_number in sorted(versions_data.iterkeys(), reverse = True):
            release_notes_versions_data += self.get_partial_html_from_version_hash(self.get_version_hash_from_version_number(version_number), self.get_version_hash_from_version_number(str(int(version_number)-1)))

        release_notes_template_data = release_notes_template_data.replace("$VERSIONS", release_notes_versions_data)

        release_notes_temp_file.write(release_notes_template_data)
        release_notes_temp_file.close()
        self.save_file_to_sftp_appcast_directory(self.get_working_path("release_notes.html"))

    def write_appcast_and_upload_to_sftp(self):
        appcast_file = open(self.get_working_path("appcast.xml"), 'w')
        appcast_file.write(self.get_appcast_data())
        appcast_file.close()
        self.save_file_to_sftp_appcast_directory(self.get_working_path("appcast.xml"))



    def get_appcast_data(self):
        appcast_template_file = open(self.get_support_files_path("appcast.template.xml"), "rU")
        contents = ""
        for line in appcast_template_file.readlines():
            contents += line
        appcast_template_file.close()

        contents = contents.replace("$TITLE", "Version " + str(self.get_current_app_version()))
        contents = contents.replace("$APP_NAME", glamour_settings["app_name"])
        contents = contents.replace("$APPCAST_LINK", self.get_https_url("appcast.xml"))
        contents = contents.replace("$RELEASE_NOTES_LINK", self.get_https_url("release_notes.html"))
        contents = contents.replace("$DESCRIPTION", "Updated to version " + str(self.get_current_app_version()))
        contents = contents.replace("$PUBLISH_DATE", str(datetime.datetime.now()))
        contents = contents.replace("$VERSION", str(self.get_current_app_version()))
        contents = contents.replace("$URL", self.get_https_url(self.get_zipfile_name()))
        return contents
        

    def zip_app_and_upload_to_sftp(self):
        print("Compressing " + glamour_settings["app_name"]+".app ... ", end = '')
        
        self.zip_folder(glamour_settings["built_app_path"], os.path.splitext(self.get_zipfile_name())[0], working_directory)
        
        print("Compressed to " + str(round(float(os.path.getsize(self.get_working_path(self.get_zipfile_name())))/float(1000**2), 2))+ " MB")
       
        self.save_file_to_sftp_appcast_directory(self.get_working_path(self.get_zipfile_name()))
        

    def save_file_to_sftp_appcast_directory(self, file_path):
        connected = False

        if self.sftp_password == None:
            self.sftp_password = getpass.getpass("Please enter your SFTP password: ")

        while not connected:
            try:
                transport = paramiko.Transport((glamour_settings["sftp_host"], glamour_settings["sftp_port"]))
                transport.connect(username = glamour_settings["sftp_username"], password = self.sftp_password)
                connected = True
                break
            except paramiko.AuthenticationException:
                self.sftp_password = getpass.getpass("Please enter your SFTP password: ")

        sftp = paramiko.SFTPClient.from_transport(transport)

        print("Uploading " +os.path.basename(file_path)+" to sftp." + glamour_settings["sftp_host"] + " ... ", end = '')
        then = time.time()
        sftp.put(localpath=file_path, remotepath = self.get_sftp_directory(os.path.basename(file_path)) )
        now = time.time()
 
        #let's do a little speed calculation for the kids back home
        Kb_per_second = 8*(float(os.path.getsize(file_path))/float(1000))/float(now-then)
        print("Finished uploading in " + str(round(now - then, 1)) + " seconds (" + str(int(round(Kb_per_second, 0))) + " Kb/s)")

    
        
    def get_partial_html_from_version_hash(self, version_hash, previous_version_hash):
        
        repo = self.get_git_repo()
        this_partial = ""
        partial_reference = open(self.get_support_files_path("release_notes.version.template.html"), 'r')
        for line in partial_reference.readlines():
            this_partial += line

        this_partial = this_partial.replace("$APPNAME", glamour_settings["app_name"])
        this_partial = this_partial.replace("$VERSION", version_hash["human_version"])
        this_partial = this_partial.replace("$HEAD", version_hash["head"])
        this_partial = this_partial.replace("$DATE", str(version_hash["date"]))
        
        if previous_version_hash is None:
            commits_between_previous_verson_and_current_version = self.get_commits_between(None, version_hash["head"])
        else:
            commits_between_previous_verson_and_current_version = self.get_commits_between(previous_version_hash["head"], version_hash["head"])
        
        commit_messages = ""

        for commit in commits_between_previous_verson_and_current_version:
          commit_messages += "<li>"+commit.message.rstrip()+"</li>\n"
        if len(commit_messages) < 1:
          commit_messages += "<li><em>Unknown changes.</em></li>"
    
        this_partial = this_partial.replace("$FEATURELIST", commit_messages)

        return this_partial

    def zip_folder(self, source_folder, zipfile_name, destination_folder):
        os.chdir(source_folder)
        return shutil.make_archive(destination_folder+"/"+zipfile_name, "zip", source_folder+"/..", glamour_settings["app_name"]+".app")

    def get_versions_data(self):
        try:
            versions_data = yaml.load(urllib2.urlopen(self.get_https_url("releases.yml")))
        except urllib2.HTTPError:
            return {str(self.get_current_app_version()): {"head": self.get_current_head_id(), "date": str(datetime.datetime.now()), "human_version": self.get_human_version(self.get_current_app_version())}}

        versions_data[str(self.get_current_app_version())] = {"head": self.get_current_head_id(), "date": str(datetime.datetime.now()), "human_version": self.get_human_version(self.get_current_app_version())}

        return versions_data

    def get_commits_between(self, commit_1, commit_2_inclusive):
        repo = self.get_git_repo()
        if commit_1 is None:
            return repo.iter_commits(commit_2_inclusive)
        else:
            return repo.iter_commits(commit_1 + ".." + commit_2_inclusive)

    def get_git_repo(self):
        repo = Repo(glamour_settings["git_repo_path"])
        if repo.bare:
            raise Error
        return repo

    def get_current_head_id(self):
        return self.get_git_repo().commit('master').name_rev.rsplit()[0]

    def get_version_hash_from_version_number(self, version_number):
        versions_data = self.get_versions_data()
        try:
            return versions_data[str(version_number)]
        except KeyError:
            return None


    def get_human_version(self, version):
        return "b"+str(version)

    def get_support_files_path(self, file_path):
        return script_directory + "/support_files/" + file_path

    def get_working_path(self, file_path):
        return working_directory + "/" + file_path

    def get_https_url(self, file_name):
        return glamour_settings["https_base_url"] + "/" +file_name

    def get_sftp_directory(self, file_name):
        return glamour_settings["sftp_appcast_directory"] + "/" +file_name 

    def get_current_app_version(self):
        plist = plistlib.readPlist(glamour_settings["built_app_path"]+"/Contents/Info.plist")
        return int(plist["CFBundleVersion"])


    def get_zipfile_name(self):
        return glamour_settings["app_name"]+"_"+str(self.get_current_app_version())+".app.zip"

        



glamour = glamour()
try:
    glamour.release(make_clean = False)
except KeyboardInterrupt:
    #even if keyboard interrupt is called clean the local files.
    glamour.clean_local()
    sys.exit(0)