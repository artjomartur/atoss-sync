using terms from application "Mail"
    on perform mail action with messages theMessages for rule theRule
        set tempFolder to POSIX path of (path to downloads folder) & "atoss_temp/"
        do shell script "mkdir -p " & quoted form of tempFolder
        
        tell application "Mail"
            repeat with theMessage in theMessages
                repeat with theAttachment in mail attachments of theMessage
                    if name of theAttachment ends with ".pdf" then
                        set savePath to tempFolder & name of theAttachment
                        save theAttachment in POSIX file savePath
                        
                        -- Execute Python script from venv
                        set pythonPath to "/Users/artjombecker/GitHub/atoss-sync/venv/bin/python3"
                        set scriptPath to "/Users/artjombecker/GitHub/atoss-sync/atoss_sync.py"
                        
                        try
                            do shell script pythonPath & " " & quoted form of scriptPath & " " & quoted form of savePath
                        on error errMsg
                            display notification "ATOSS Sync Error: " & errMsg with title "Sync Failed"
                        end try
                        
                        -- Optional: Delete the temp file after processing
                        -- do shell script "rm " & quoted form of savePath
                    end if
                end repeat
            end repeat
        end tell
    end perform mail action with messages
end using terms from
