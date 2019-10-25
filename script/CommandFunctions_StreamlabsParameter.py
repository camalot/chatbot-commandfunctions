#---------------------------------------
#   Import Libraries
#---------------------------------------
import sys
import clr
import json
import codecs
import os
import re
import random
import datetime
import glob
import time
import threading
import shutil
import tempfile
from HTMLParser import HTMLParser
import argparse

clr.AddReference("IronPython.SQLite.dll")
clr.AddReference("IronPython.Modules.dll")

# clr.AddReferenceToFileAndPath(os.path.join(os.path.dirname(
#     os.path.realpath(__file__)), "./libs/ChatbotSystem.dll"))
# import ChatbotSystem


#---------------------------------------
#   [Required] Script Information
#---------------------------------------
ScriptName = "Command Functions"
Website = "http://darthminos.tv"
Description = "Command Functions that let you replace, call json urls, etc"
Creator = "DarthMinos"
Version = "1.0.0-snapshot"
Repo = "camalot/chatbot-commandfunctions"

DonateLink = "https://paypal.me/camalotdesigns"
ReadMeFile = "https://github.com/" + Repo + "/blob/develop/ReadMe.md"

REPLACE_REGEX = re.compile(r'\$replace\s+(--input[=\s](.+))\s+(--find[=\s](.+))\s+(--replace[=\s](.+))', re.U)
CUSTOMAPIJSON_REGEX = re.compile(r"\$customapijson\(([^,]+),\s*([^\)]+)\)", re.U)
RAWTEXT_REGEX = re.compile(r'^\s*\{([^\}]+)\}$', re.U)
SCENE_REGEX = re.compile(
    r'\$scene\s+(--name)[=\s](?P<name>(?:[\'\"][^\'\"]+[\'\"]|.+?))(?:\s+--scene2[=\s](?P<scene2>.+)\s+(?:--seconds[=\s](?P<seconds>\d+)))?(?:\s|$|\n)', re.U)
SOURCE_REGEX = re.compile(
    r'\$source\s+(--name)[=\s](?P<name>.+?)\s+(?:(--enabled)[=\s](?P<enabled>.+?)|--seconds[=\s](?<seconds>\d+))(?:\s+(--scene)[=\s](?P<scene>.+?))?(?:\s+|$|\n)', re.U)

def Init():
    return

def Unload():
    return

def Parse(parseString, user, target, message):
    resultString = parseString

    resultString = ParseCustomApiJson(parseString, user, target, message)
    resultString = ObsSceneParse(parseString, user, target, message)
    resultString = ObsSourceParse(parseString, user, target, message)
    ### LAST
    resultString = ParseReplace(parseString, user, target, message)
    resultString = StopStreamParse(parseString, user, target, message)
    return resultString

def ObsSceneParse(parseString, user, target, message):
    resultString = parseString
    # $scene --name="my scene"
    if "$scene" in resultString:

        # Apply regex to verify correct parameter use
        result = SCENE_REGEX.search(resultString)
        if result:
            # Get results from regex match
            fullParameterMatch = result.group(0)
            scene = result.group("name")
            scene2 = result.group("scene2") if "scene2" in result.groupdict() else None
            seconds = result.group("seconds") if "seconds" in result.groupdict() else None

            rep = ReplaceObject()
            rargs = argparse.ArgumentParser(prog=ScriptName)
            rargs.add_argument("--name", action='store', required=True)
            rargs.add_argument("--scene2", action='store', required=True)
            rargs.add_argument("--seconds", action='store', required=True)
            rargs.parse_args([
                "--name", scene,
                "--scene2", scene2 if scene2 else None,
                "--seconds", stripQuotes(seconds) if seconds else "0"
                ], namespace=rep)

            # Call OBS Current Scene
            Parent.SetOBSCurrentScene(stripQuotes(rep.name), CallbackLogger)
            # A vailid time given?
            if int(rep.seconds) > 0 and rep.scene2:
                # Start a new thread to swap to scene2 after amount of given seconds
                threading.Thread(target=SwapSceneTimer,
                                 args=(stripQuotes(rep.scene2), int(rep.seconds))).start()

            # Replace the whole parameter with an empty string
            resultString = resultString.replace(fullParameterMatch, "")
    return resultString

def ObsSourceParse(parseString, user, target, message):
    resultString = parseString
    # $OBSsource("source", "enabled")
    # $OBSsource("source", "enabled", "scene")
    if "$source" in resultString:
        Parent.Log(ScriptName, "found $source")
        # Apply regex to verify correct parameter use
        result = SOURCE_REGEX.search(resultString)
        if result:
            # Get match groups from regex
            fullParameterMatch = result.group(0)
            Parent.Log(ScriptName, "MATCH: " + fullParameterMatch)
            source = result.group("name")
            enabled = result.group("enabled") if "enabled" in result.groupdict() else None
            seconds = result.group("seconds") if "seconds" in result.groupdict() else None
            scene = result.group("scene") if "scene" in result.groupdict() else None

            # if they are doing timmer, enabled should be true
            if enabled is None:
                enabled = "true"
            if seconds is None:
                seconds = "0"

            rep = ReplaceObject()
            rargs = argparse.ArgumentParser(prog=ScriptName)
            rargs.add_argument("--name", action='store', required=True)
            rargs.add_argument("--enabled", action='store', required=True)
            rargs.add_argument("--seconds", action='store', required=True)
            rargs.add_argument("--scene", action='store')
            rargs.parse_args(["--name", source.strip(), 
                              "--enabled", enabled.strip(),
                              "--seconds", stripQuotes(seconds),
                              "--scene", scene if scene.strip() else None], namespace=rep)

            Parent.Log(ScriptName, "name: " + stripQuotes(rep.name))
            Parent.Log(ScriptName, "enabled: " + rep.enabled)
            Parent.Log(ScriptName, "seconds: " + rep.seconds)
            Parent.Log(ScriptName, "scene: " + stripQuotes(rep.scene))

            Parent.SetOBSSourceRender(stripQuotes(rep.name), str2bool(
                rep.enabled), stripQuotes(rep.scene), CallbackLogger)
            if int(rep.seconds) > 0:

                Parent.Log(ScriptName, "Set Disable: " + str(rep.seconds) + " seconds")
                # Start a new thread to disable the source again after amount of given seconds
                threading.Thread(target=DisableSourceTimer, args=(
                    stripQuotes(rep.name), int(rep.seconds), stripQuotes(rep.scene))).start()

            # Replace the whole parameter with an empty string
            resultString = resultString.replace(fullParameterMatch, "")
    return resultString

def StopStreamParse(parseString, user, target, message):
    if Parent.HasPermission(user, "Moderator", ""):
        # $stopstream parameter
        if "$stopstream" in parseString:
            Parent.StopOBSStreaming(CallbackLogger)
            return parseString.replace("$stopstream", "")

def ParseReplace(parseString, user, target, message):
    # EXAMPLE: $replace --input $customapijson(url, foo.bar) --find some string --replace another-string
    #   INPUT: { "foo": { "bar": "we found some string" } }
    #  OUTPUT: we found another-string
    resultString = parseString
    if "$replace" in resultString:
        result = REPLACE_REGEX.search(resultString)
        if result:
            rep = ReplaceObject()
            rargs = argparse.ArgumentParser(prog=ScriptName)
            rargs.add_argument("--input", action='store', required=True)
            rargs.add_argument("--find", action='store', required=True)
            rargs.add_argument("--replace", action='store', required=True)
            rargs.parse_args([
                result.group(1).strip(),
                result.group(2).strip(),
                result.group(3).strip(),
                result.group(4).strip(),
                result.group(5).strip(),
                result.group(6).strip()], namespace=rep)
            fullMatch = result.group(0)
            resultString = resultString.Replace(
                fullMatch, rep.input.Replace(rep.find, rep.replace))
    return resultString

def ParseCustomApiJson(parseString, user, target, message):
    resultString = parseString
    if "$customapijson" in resultString:
        result = CUSTOMAPIJSON_REGEX.search(resultString)
        if result:
            fullMatch = result.group(0)
            url = result.group(1).strip()
            args = result.group(2).strip().split(",")
            jresp = json.loads(Parent.GetRequest(
                url, {"Accept": "application/json"}))
            if jresp['status'] == 200:
                resp = json.loads(jresp['response'])
                h = HTMLParser()
                output = ""
                for a in args:
                    amatch = RAWTEXT_REGEX.search(a.strip())
                    if amatch:
                        output += amatch.group(1)
                    else:
                        output += h.unescape(rsearch(resp, a.strip())).strip()
                resultString = resultString.Replace(
                    fullMatch, output.Replace('\\n', '\n').strip())
            else:
                Parent.Log(ScriptName, "STATUS: " + str(jresp['status']))
    return resultString


###########################
# Obs Remote Functions
###########################


def CallbackLogger(response):
    """ Logs callback error response in scripts logger. """
    parsedresponse = json.loads(response)
    if parsedresponse["status"] == "error":
        Parent.Log(ScriptName, parsedresponse["error"])
    return


def DisableSourceTimer(source, seconds, scene):
    """ Disables a given source in optional scene after given amount of seconds. """
    counter = 0
    while counter < seconds:
        time.sleep(1)
        counter += 1
    Parent.SetOBSSourceRender(source, False, scene, CallbackLogger)
    return


def SwapSceneTimer(scene, seconds):
    """ Swaps to a given secene after given amount of seconds. """
    counter = 0
    while counter < seconds:
        time.sleep(1)
        counter += 1
    Parent.SetOBSCurrentScene(scene, CallbackLogger)
    return


def str2bool(v):
    if not v:
        return False
    return stripQuotes(v).strip().lower() in ("yes", "true", "1", "t", "y")

def stripQuotes(v):
    r = re.compile(r"^[\"\'](.*)[\"\']$", re.U)
    m = r.search(v)
    if m:
        return m.group(1)
    return v
class ReplaceObject(object):
    pass

def rsearch(obj, search):
    arr = search.split(".")
    if len(arr) > 0:
        item = arr[0]
        arr.remove(item)
        result = obj.get(item, None)
        if result:
            if len(arr) > 0:
                return rsearch(result, ".".join(arr))
            else:
                return result
        else:
            return ""
    else:
        return obj

def OpenScriptUpdater():
    currentDir = os.path.realpath(os.path.dirname(__file__))
    chatbotRoot = os.path.realpath(os.path.join(currentDir, "../../../"))
    libsDir = os.path.join(currentDir, "libs/updater")
    Parent.Log(ScriptName, libsDir)
    try:
        src_files = os.listdir(libsDir)
        tempdir = tempfile.mkdtemp()
        Parent.Log(ScriptName, tempdir)
        for file_name in src_files:
            full_file_name = os.path.join(libsDir, file_name)
            if os.path.isfile(full_file_name):
                Parent.Log(ScriptName, "Copy: " + full_file_name)
                shutil.copy(full_file_name, tempdir)
        updater = os.path.join(tempdir, "ChatbotScriptUpdater.exe")
        updaterConfigFile = os.path.join(tempdir, "update.manifest")
        repoVals = Repo.split('/')
        updaterConfig = {
            "path": os.path.realpath(os.path.join(currentDir, "../")),
            "version": Version,
            "name": ScriptName,
            "requiresRestart": True,
            "kill": [],
            "execute": {
                "before": [],
                "after": []
            },
            "chatbot": os.path.join(chatbotRoot, "Streamlabs Chatbot.exe"),
            "script": os.path.basename(os.path.dirname(os.path.realpath(__file__))),
            "website": Website,
            "repository": {
                "owner": repoVals[0],
                "name": repoVals[1]
            }
        }
        Parent.Log(ScriptName, updater)
        configJson = json.dumps(updaterConfig)
        Parent.Log(ScriptName, configJson)
        with open(updaterConfigFile, "w+") as f:
            f.write(configJson)
        os.startfile(updater)
        return
    except OSError as exc:  # python >2.5
        raise
    return


def OpenFollowOnTwitchLink():
    os.startfile("https://twitch.tv/DarthMinos")
    return


def OpenReadMeLink():
    os.startfile(ReadMeFile)
    return


def OpenDonateLink():
    os.startfile(DonateLink)
    return
