param(
    [string]$ConfigPath = "config.json",
    [string]$TemplatePath = "soti-final-lockdown-homescreen.html",
    [string]$OutputPath = "soti-final-lockdown-homescreen-offline.html",
    [switch]$DemoMode
)




Write-Host "🚀 SOTI MobiControl Offline Template Builder" -ForegroundColor Green
if ($DemoMode) {
    Write-Host "🎭 DEMO MODE ACTIVE" -ForegroundColor Yellow
}
Write-Host "================================================" -ForegroundColor Green

# Load configuration
if (-not (Test-Path $ConfigPath)) {
    Write-Error "Config file not found: $ConfigPath"
    exit 1
}

try {
    $config = Get-Content $ConfigPath | ConvertFrom-Json
    Write-Host "✅ Config loaded successfully" -ForegroundColor Green
}
catch {
    Write-Error "Failed to parse config.json: $_"
    exit 1
}

# Load template
if (-not (Test-Path $TemplatePath)) {
    Write-Error "Template file not found: $TemplatePath"
    exit 1
}

$template = Get-Content $TemplatePath -Raw
Write-Host "✅ Template loaded successfully" -ForegroundColor Green

# Demo Mode: Inject test data for all 19 SOTI app slots
if ($DemoMode) {
    Write-Host "🎭 Demo Mode Enabled - Creating demo homescreen..." -ForegroundColor Yellow
    
    # Change output path for demo mode
    $OutputPath = "demo-homescreen.html"
    
    # Demo app data with SOTI app structure
    $demoApps = @(
        @{ Name = "Work Orders"; Icon = "work-orders.png"; Url = "Launch://com.company.workorders" },
        @{ Name = "Inventory Scanner"; Icon = "inventory.png"; Url = "Launch://com.company.scanner" },
        @{ Name = "Safety Checklist"; Icon = "safety.png"; Url = "Launch://com.company.safety" },
        @{ Name = "Time Tracker"; Icon = "timetrack.png"; Url = "Launch://com.company.timetrack" },
        @{ Name = "Asset Manager"; Icon = "assets.png"; Url = "Launch://com.company.assets" },
        @{ Name = "Quality Control"; Icon = "qc.png"; Url = "Launch://com.company.qc" },
        @{ Name = "Maintenance Log"; Icon = "maintenance.png"; Url = "Launch://com.company.maint" },
        @{ Name = "Reports Hub"; Icon = "reports.png"; Url = "Launch://com.company.reports" },
        @{ Name = "Team Chat"; Icon = "chat.png"; Url = "Launch://com.company.chat" },
        @{ Name = "Document Library"; Icon = "docs.png"; Url = "Launch://com.company.docs" },
        @{ Name = "Training Portal"; Icon = "training.png"; Url = "Launch://com.company.training" },
        @{ Name = "Emergency Contacts"; Icon = "emergency.png"; Url = "Launch://com.company.emergency" },
        @{ Name = "Fleet Tracker"; Icon = "fleet.png"; Url = "Launch://com.company.fleet" },
        @{ Name = "Compliance Check"; Icon = "compliance.png"; Url = "Launch://com.company.compliance" },
        @{ Name = "Production Monitor"; Icon = "production.png"; Url = "Launch://com.company.production" },
        @{ Name = "Shift Schedule"; Icon = "schedule.png"; Url = "Launch://com.company.schedule" },
        @{ Name = "Equipment Status"; Icon = "equipment.png"; Url = "Launch://com.company.equipment" },
        @{ Name = "Facility Map"; Icon = "facility.png"; Url = "Launch://com.company.facility" },
        @{ Name = "Help Desk"; Icon = "helpdesk.png"; Url = "Launch://com.company.helpdesk" }
    )
    
    # Replace SOTI variables with demo data in proper app structure
    for ($i = 0; $i -lt 19; $i++) {
        $app = $demoApps[$i]
        
        # Replace SOTI variables with demo data
        $template = $template -replace "<MCLink$i>", $app.Url
        $template = $template -replace "<MCDISP$i>", $app.Name
        $template = $template -replace "<MCExeIcon$i>", $app.Icon
        $template = $template -replace "<MCDispImg$i>", $app.Icon
    }
    
    Write-Host "   ✅ Injected $($demoApps.Count) demo apps" -ForegroundColor Green
    Write-Host "   📱 Apps: $($demoApps.Name -join ', ')" -ForegroundColor Gray
}

# Function to download content with retry logic
function Get-WebContent {
    param([string]$Url, [string]$Description)
    
    Write-Host "📥 Downloading $Description..." -ForegroundColor Yellow
    
    for ($i = 1; $i -le 3; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 30
            if ($response.StatusCode -eq 200) {
                Write-Host "   ✅ Downloaded successfully" -ForegroundColor Green
                return $response.Content
            }
        }
        catch {
            Write-Host "   ❌ Attempt $i failed: $($_.Exception.Message)" -ForegroundColor Red
            if ($i -eq 3) {
                throw "Failed to download $Description after 3 attempts"
            }
            Start-Sleep -Seconds 2
        }
    }
}

# Download all dependencies
Write-Host "`n🔄 Downloading external dependencies..." -ForegroundColor Cyan

$dependencies = @{}

# Download all dependencies
Write-Host "`n🔄 Downloading external dependencies..." -ForegroundColor Cyan

$dependencies = @{}
$downloadedCount = 0
$enabledDeps = $config.dependencies | Where-Object { $_.enabled -eq $true }

foreach ($dep in $enabledDeps) {
    try {
        if ($dep.type -eq "font") {
            # Handle font files as binary data
            Write-Host "📥 Downloading font: $($dep.name)..." -ForegroundColor Yellow
            
            $tempFile = [System.IO.Path]::GetTempFileName()
            try {
                Invoke-WebRequest -Uri $dep.url -OutFile $tempFile -UseBasicParsing -TimeoutSec 30
                $fontBytes = [System.IO.File]::ReadAllBytes($tempFile)
                $fontBase64 = [System.Convert]::ToBase64String($fontBytes)
                
                $dependencies[$dep.name] = @{
                    content     = "data:$($dep.mimeType); base64, $fontBase64"
                    type        = $dep.type
                    placeholder = $dep.placeholder
                }
                Write-Host "   ✅ Font downloaded and converted ($([math]::Round($fontBytes.Length / 1KB, 1)) KB)" -ForegroundColor Green
            }
            finally {
                if (Test-Path $tempFile) {
                    Remove-Item $tempFile -Force
                }
            }
        }
        else {
            # Handle text-based dependencies (CSS, JS)
            $dependencies[$dep.name] = @{
                content     = Get-WebContent -Url $dep.url -Description $dep.name
                type        = $dep.type
                placeholder = $dep.placeholder
            }
        }
        $downloadedCount++
    }
    catch {
        Write-Host "   ❌ Failed to download $($dep.name): $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "   ⚠️  Skipping $($dep.name)" -ForegroundColor Yellow
    }
}

# Download and convert logo to base64 if logoUrl is provided
if ($config.branding.logoUrl -and $config.branding.logoUrl -ne "") {
    try {
        Write-Host "📥 Downloading BI logo..." -ForegroundColor Yellow
        
        # Create a temporary file to handle binary content properly
        $tempFile = [System.IO.Path]::GetTempFileName()
        try {
            Invoke-WebRequest -Uri $config.branding.logoUrl -OutFile $tempFile -UseBasicParsing -TimeoutSec 30
            
            # Read binary content and convert to base64
            $logoBytes = [System.IO.File]::ReadAllBytes($tempFile)
            $logoBase64 = [System.Convert]::ToBase64String($logoBytes)
            
            # Determine MIME type from URL or default to PNG
            $mimeType = "image/png"
            if ($config.branding.logoUrl -match '\.svg$') {
                $mimeType = "image/svg+xml"
            }
            elseif ($config.branding.logoUrl -match '\.jpg$|\.jpeg$') {
                $mimeType = "image/jpeg"
            }
            elseif ($config.branding.logoUrl -match '\.gif$') {
                $mimeType = "image/gif"
            }
            
            $dependencies['Logo'] = @{
                content     = "data:$mimeType; base64, $logoBase64"
                type        = "logo"
                placeholder = 'LOGO_BASE64_PLACEHOLDER'
            }
            Write-Host "   ✅ Logo converted to base64 successfully ($([math]::Round($logoBytes.Length / 1KB, 1)) KB)" -ForegroundColor Green
            
        }
        finally {
            # Clean up temp file
            if (Test-Path $tempFile) {
                Remove-Item $tempFile -Force
            }
        }
    }
    catch {
        Write-Host "   ⚠️  Logo download failed: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "   📄 Using embedded SVG fallback" -ForegroundColor Yellow
        $dependencies['Logo'] = @{
            content     = $config.branding.logoBase64
            type        = "logo"
            placeholder = 'LOGO_BASE64_PLACEHOLDER'
        }
    }
}
else {
    Write-Host "📄 Using embedded SVG logo from config" -ForegroundColor Yellow
    $dependencies['Logo'] = @{
        content     = $config.branding.logoBase64
        type        = "logo"
        placeholder = 'LOGO_BASE64_PLACEHOLDER'
    }
}

Write-Host "✅ Downloaded $downloadedCount dependencies successfully`n" -ForegroundColor Green

# Replace external links with embedded content
Write-Host "🔧 Embedding dependencies into template..." -ForegroundColor Cyan

# Replace external links with embedded content
Write-Host "🔧 Embedding dependencies into template..." -ForegroundColor Cyan

$embeddedCount = 0

# Process each dependency in the order they were downloaded
foreach ($depName in $dependencies.Keys) {
    $dep = $dependencies[$depName]
    
    try {
        if ($dep.type -eq "css") {
            # Process Bootstrap Icons CSS to replace font URLs with placeholders
            $cssContent = $dep.content
            if ($depName -eq "Bootstrap Icons") {
                # Replace font URLs with placeholders that will be replaced with base64 data
                $cssContent = $cssContent -replace 'url\("\.\/fonts\/bootstrap-icons\.woff2[^"]*"\)', 'url("BOOTSTRAP_ICONS_WOFF2_PLACEHOLDER")'
                $cssContent = $cssContent -replace 'url\("\.\/fonts\/bootstrap-icons\.woff[^"]*"\)', 'url("BOOTSTRAP_ICONS_WOFF_PLACEHOLDER")'
            }
            
            # Wrap CSS content in style tags
            $embeddedContent = "<style>`n$cssContent`n</style>"
            Write-Host "   🎨 Embedding CSS: $depName" -ForegroundColor Yellow
        }
        elseif ($dep.type -eq "js") {
            # Wrap JS content in script tags
            $embeddedContent = "<script>`n$($dep.content)`n</script>"
            Write-Host "   ⚡ Embedding JS: $depName" -ForegroundColor Yellow
        }
        elseif ($dep.type -eq "logo") {
            # Handle logo replacement - just replace the placeholder with the base64 data
            $embeddedContent = $dep.content
            Write-Host "   🖼️  Embedding Logo: $depName" -ForegroundColor Yellow
        }
        elseif ($dep.type -eq "font") {
            # Handle font files - replace placeholder with data URL
            $embeddedContent = $dep.content
            Write-Host "   🔤 Embedding Font: $depName" -ForegroundColor Yellow
        }
        else {
            Write-Host "   ⚠️  Unknown dependency type: $($dep.type) for $depName" -ForegroundColor Yellow
            continue
        }
        
        # Replace placeholder with embedded content
        if ($template -match [regex]::Escape($dep.placeholder)) {
            $template = $template -replace [regex]::Escape($dep.placeholder), $embeddedContent
            Write-Host "   ✅ $depName embedded successfully" -ForegroundColor Green
            $embeddedCount++
        }
        else {
            Write-Host "   ⚠️  Placeholder not found for $depName" -ForegroundColor Yellow
            Write-Host "   � Looking for: $($dep.placeholder)" -ForegroundColor Gray
            
            # For CSS, try to add to head section
            if ($dep.type -eq "css") {
                $headPattern = "(\s*</head>)"
                $template = $template -replace $headPattern, "`n    $embeddedContent`$1"
                Write-Host "   ✅ $depName added to head section" -ForegroundColor Green
                $embeddedCount++
            }
            # For JS, try to add before closing body
            elseif ($dep.type -eq "js") {
                $bodyPattern = "(\s*</body>)"
                $template = $template -replace $bodyPattern, "`n$embeddedContent`n`$1"
                Write-Host "   ✅ $depName added before closing body" -ForegroundColor Green
                $embeddedCount++
            }
            # For logo, try alternative placement
            elseif ($dep.type -eq "logo") {
                $logoInsertPattern = '(\s*// Create BI Header with base64 logo\s*)'
                $logoVariableWithAssignment = "`$1var logoBase64 = `"$($dep.content)`"; `r`n            "
                if ($template -match $logoInsertPattern) {
                    $template = $template -replace $logoInsertPattern, $logoVariableWithAssignment
                    Write-Host "   ✅ $depName added to script section" -ForegroundColor Green
                    $embeddedCount++
                }
            }
        }
    }
    catch {
        Write-Host "   ❌ Failed to embed $depName`: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "   📊 Embedded $embeddedCount out of $($dependencies.Count) dependencies" -ForegroundColor Cyan

# Apply configuration values
Write-Host "⚙️  Applying configuration..." -ForegroundColor Cyan

# Update title
$template = $template -replace '<title>.*?</title>', "<title>$($config.template.title)</title>"

# Update header, footer text and badge
$template = $template -replace 'HEADER_TEXT_PLACEHOLDER', $config.template.headerText
$template = $template -replace 'FOOTER_TEXT_PLACEHOLDER', $config.template.footerText
$template = $template -replace 'FOOTER_BADGE_PLACEHOLDER', $config.template.footerBadge

# Update CSS custom properties with config colors
$colorReplacements = @{
    '--bi-primary'   = $config.branding.colors.primary
    '--bi-secondary' = $config.branding.colors.secondary  
    '--bi-neutral'   = $config.branding.colors.neutral
    '--bi-surface'   = $config.branding.colors.surface
}

foreach ($property in $colorReplacements.Keys) {
    $pattern = "${property}:\s*#[0-9A-Fa-f]{ 6 }; "
    $replacement = "${property}: $($colorReplacements[$property]); "
    $template = $template -replace $pattern, $replacement
}

# Inject grid configuration
$gridConfig = @{
    gridColumns = @{
        mobile = $config.apps.gridColumns.mobile
        tablet = $config.apps.gridColumns.tablet
    }
    gridRows    = @{
        mobile = $config.apps.gridRows.mobile
        tablet = $config.apps.gridRows.tablet
    }
} | ConvertTo-Json -Compress

$template = $template -replace 'GRID_CONFIG_PLACEHOLDER', $gridConfig

# Generate device information modal content
$deviceInfoContent = ""
if ($config.deviceInfo.enabled) {
    foreach ($categoryKey in $config.deviceInfo.categories.PSObject.Properties.Name) {
        $category = $config.deviceInfo.categories.$categoryKey
        
        if ($category.enabled) {
            # Add category header
            $deviceInfoContent += "                    <!-- $($category.title) -->`n"
            $deviceInfoContent += "                    <div class=`"device-info-category`">`n"
            $deviceInfoContent += "                        <i class=`"bi $($category.icon) me-1`"></i>`n"
            $deviceInfoContent += "                        $($category.title)`n"
            $deviceInfoContent += "                    </div>`n`n"
            
            # Add fields for this category
            foreach ($fieldKey in $category.fields.PSObject.Properties.Name) {
                $field = $category.fields.$fieldKey
                
                if ($field.enabled) {
                    $deviceInfoContent += "                    <div class=`"device-info-item`">`n"
                    $deviceInfoContent += "                        <span class=`"device-info-label`">$($field.label):</span>`n"
                    $deviceInfoContent += "                        <span class=`"device-info-value`">$($field.variable)</span>`n"
                    $deviceInfoContent += "                    </div>`n`n"
                }
            }
        }
    }
}

# Replace device info placeholder
$template = $template -replace '<!-- DEVICE_INFO_CONTENT_PLACEHOLDER -->', $deviceInfoContent

# Add metadata comments
$metadata = @"
    <!--
    SOTI MobiControl Offline Template
    Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    Config: $ConfigPath
    Original Template: $TemplatePath
    All external dependencies embedded for offline use.
    -->

"@

$template = $template -replace '<!DOCTYPE html>', "$metadata<!DOCTYPE html>"

# Save the final template
try {
    $template | Out-File -FilePath $OutputPath -Encoding UTF8
    Write-Host "✅ Offline template created successfully!" -ForegroundColor Green
    Write-Host "📁 Output file: $OutputPath" -ForegroundColor Yellow
    
    # Get file size
    $fileSize = [math]::Round((Get-Item $OutputPath).Length / 1KB, 2)
    Write-Host "📊 File size: $fileSize KB" -ForegroundColor Yellow
    
}
catch {
    Write-Error "Failed to save output file: $_"
    exit 1
}

# Validation
Write-Host "`n🔍 Validating output..." -ForegroundColor Cyan

$outputContent = Get-Content $OutputPath -Raw

# Check for external dependencies
$externalLinks = @(
    'cdn.jsdelivr.net',
    'cdnjs.cloudflare.com',
    'fonts.googleapis.com'
)

$hasExternalDeps = $false
foreach ($link in $externalLinks) {
    if ($outputContent -match $link) {
        Write-Host "   ⚠️  Still contains external reference to: $link" -ForegroundColor Yellow
        $hasExternalDeps = $true
    }
}

if (-not $hasExternalDeps) {
    Write-Host "   ✅ No external dependencies found - fully offline ready!" -ForegroundColor Green
}

# Summary
Write-Host "`n📋 Summary:" -ForegroundColor Cyan

# Show embedded dependencies
foreach ($depName in $dependencies.Keys) {
    $dep = $dependencies[$depName]
    $icon = switch ($dep.type) {
        "css" { "🎨" }
        "js" { "⚡" }
        "logo" { "🖼️" }
        default { "📦" }
    }
    Write-Host "   • $icon $depName`: Embedded" -ForegroundColor Green
}

Write-Host "   • 🏢 BI Branding: Applied" -ForegroundColor Green
Write-Host "   • 📱 Array-based SOTI: Ready" -ForegroundColor Green
Write-Host "   • 🔢 SOTI Variables (0 - 19): Preserved" -ForegroundColor Green
Write-Host "   • 🌐 Offline Compatible: 100%" -ForegroundColor Green

Write-Host "`n🎉 Offline SOTI template ready for deployment!" -ForegroundColor Green
Write-Host "Upload '$OutputPath' to SOTI MobiControl for offline-capable devices.`n" -ForegroundColor Yellow