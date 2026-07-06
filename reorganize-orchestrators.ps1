`$v3_5 = "c:\Users\Mike\Documents\Github\AIOS\aios-workshop-instructions\templates\agents\orchestrator.v3.5.agent.md"
`$v4 = "c:\Users\Mike\Documents\Github\AIOS\aios-workshop-instructions\templates\agents\orchestrator.v4.agent.md"
`$v5 = "c:\Users\Mike\Documents\Github\AIOS\aios-workshop-instructions\templates\agents\orchestrator.v5.agent.md"

# Step 1: Copy v4 to v5
Copy-Item -Path `$v4 -Destination `$v5 -Force
Write-Host "Created v5 from v4"

# Step 2: Delete v4
Remove-Item -Path `$v4 -Force
Write-Host "Deleted v4"

# Step 3: Copy v3.5 to v4
Copy-Item -Path `$v3_5 -Destination `$v4 -Force
Write-Host "Created v4 from v3.5"

# Step 4: Delete v3.5
Remove-Item -Path `$v3_5 -Force
Write-Host "Deleted v3.5"

Write-Host "Reorganization complete!"
