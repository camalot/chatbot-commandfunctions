# CHATBOT COMMAND FUNCTIONS
[![CHATBOT COMMAND FUNCTIONS](https://github.com/camalot/chatbot-commandfunctions/actions/workflows/build.yml/badge.svg)](https://github.com/camalot/chatbot-commandfunctions/actions/workflows/build.yml)

Adds functions to use in your commands


## REQUIREMENTS

- Install [StreamLabs Chatbot](https://streamlabs.com/chatbot)
- [Enable Scripts in StreamLabs Chatbot](https://github.com/StreamlabsSupport/Streamlabs-Chatbot/wiki/Prepare-&-Import-Scripts)
- [Microsoft .NET Framework 4.7.2 Runtime](https://dotnet.microsoft.com/download/dotnet-framework/net472) or later

## INSTALL

- Download the latest zip file from [Releases](https://github.com/camalot/chatbot-commandfunctions/releases/latest)
- Right-click on the downloaded zip file and choose `Properties`
- Click on `Unblock`  
[![](https://i.imgur.com/vehSSn7l.png)](https://i.imgur.com/vehSSn7.png)  
  > **NOTE:** If you do not see `Unblock`, the file is already unblocked.
- In Chatbot, Click on the import icon on the scripts tab.  
  ![](https://i.imgur.com/16JjCvR.png)
- Select the downloaded zip file
- Right click on `Twitch Team` row and select `Insert API Key`. Click yes on the dialog.  
[![](https://i.imgur.com/AWmtHKFl.png)](https://i.imgur.com/AWmtHKF.png)  

## CONFIGURATION

Make sure the script is enabled  
[![](https://i.imgur.com/d8rAJN9l.png)](https://i.imgur.com/d8rAJN9.png)  

Click on the script in the list to bring up the configuration.



## REPLACE

Find and replace values in the command.

### EXAMPLE

```
$replace --input Find Some String --find some string --replace another string
```

### OUTPUT

> Find another string




## CUSTOMAPIJSON

Make an api call and return valus from a json object syntax

### USAGE

```
$customapijson(URL, ARGUMENTS...)
```

Arguments are the `json object scope` or `literal text`.

### EXAMPLE

```
$customapijson(https://api.forismatic.com/api/1.0/?method=getQuote&format=json&lang=en, {"}, quoteText, {" - }, quoteAuthor)
```

#### OUTPUT

> "Happiness is a Swedish sunset — it is there for all, but most of us look the other way and lose it." - Mark Twain


## OBS SCENE

Show a scene in OBS

### USAGE

```
$scene --name="SCENE_NAME" [--scene2="SCENE2_NAME" --seconds=7]
```

### ARGUMENTS

- `name`: The scene name to change to
- `scene2`: A scene to change to after `seconds`
- `seconds`: The number of seconds to show the scene before switching


## OBS SOURCE

Show a source in OBS

### USAGE

```
$scene --name="SOURCE_NAME" [--enabled="true"|--seconds=7] [--scene="SCENE_NAME]
```

### ARGUMENTS

- `name`: The source name to change to
- `enabled`: The enabled state of the source
- `seconds`: The number of seconds to show the source before disabling
- `scene`: The scene which the source resides. 
