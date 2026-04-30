$ErrorActionPreference = "Stop"
$vendor = "main\static\vendor"

function Download($url, $dest) {
    $dir = Split-Path $dest -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    if (Test-Path $dest) { Write-Host "  skip  $dest" -ForegroundColor DarkGray; return }
    Write-Host "  get   $url" -ForegroundColor Cyan
    Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
}

Write-Host "`n=== Bootstrap ===" -ForegroundColor Yellow
Download "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"       "$vendor\bootstrap\5.3.3\css\bootstrap.min.css"
Download "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"  "$vendor\bootstrap\5.3.3\js\bootstrap.bundle.min.js"
Download "https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css"       "$vendor\bootstrap\5.2.3\css\bootstrap.min.css"
Download "https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"  "$vendor\bootstrap\5.2.3\js\bootstrap.bundle.min.js"

Write-Host "`n=== jQuery ===" -ForegroundColor Yellow
Download "https://cdn.jsdelivr.net/npm/jquery@3.7.1/dist/jquery.min.js"  "$vendor\jquery\jquery.min.js"

Write-Host "`n=== Material Design Icons ===" -ForegroundColor Yellow
Download "https://cdn.jsdelivr.net/npm/@mdi/font@7.4.47/css/materialdesignicons.min.css"               "$vendor\mdi\css\materialdesignicons.min.css"
Download "https://cdn.jsdelivr.net/npm/@mdi/font@7.4.47/fonts/materialdesignicons-webfont.woff2"       "$vendor\mdi\fonts\materialdesignicons-webfont.woff2"
Download "https://cdn.jsdelivr.net/npm/@mdi/font@7.4.47/fonts/materialdesignicons-webfont.woff"        "$vendor\mdi\fonts\materialdesignicons-webfont.woff"
Download "https://cdn.jsdelivr.net/npm/@mdi/font@7.4.47/fonts/materialdesignicons-webfont.ttf"         "$vendor\mdi\fonts\materialdesignicons-webfont.ttf"
$mdiCss = Get-Content "$vendor\mdi\css\materialdesignicons.min.css" -Raw
$mdiCss = $mdiCss -replace '\.\./fonts/', '../fonts/'
Set-Content "$vendor\mdi\css\materialdesignicons.min.css" $mdiCss -NoNewline

Write-Host "`n=== Font Awesome ===" -ForegroundColor Yellow
Download "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.2/css/all.min.css"              "$vendor\fontawesome\css\all.min.css"
$faFonts = @(
    "fa-brands-400.woff2","fa-brands-400.ttf",
    "fa-regular-400.woff2","fa-regular-400.ttf",
    "fa-solid-900.woff2","fa-solid-900.ttf",
    "fa-v4compatibility.woff2","fa-v4compatibility.ttf"
)
foreach ($f in $faFonts) {
    Download "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.2/webfonts/$f"  "$vendor\fontawesome\webfonts\$f"
}

Write-Host "`n=== perfect-scrollbar ===" -ForegroundColor Yellow
Download "https://cdn.jsdelivr.net/npm/perfect-scrollbar@1.5.5/css/perfect-scrollbar.css"        "$vendor\perfect-scrollbar\css\perfect-scrollbar.css"
Download "https://cdn.jsdelivr.net/npm/perfect-scrollbar@1.5.5/dist/perfect-scrollbar.min.js"    "$vendor\perfect-scrollbar\js\perfect-scrollbar.min.js"

Write-Host "`n=== node-waves ===" -ForegroundColor Yellow
Download "https://cdn.jsdelivr.net/npm/node-waves@0.7.6/dist/waves.min.css"    "$vendor\node-waves\css\waves.min.css"
Download "https://cdn.jsdelivr.net/npm/node-waves@0.7.6/dist/waves.min.js"     "$vendor\node-waves\js\waves.min.js"

Write-Host "`n=== bootstrap-datepicker ===" -ForegroundColor Yellow
Download "https://cdn.jsdelivr.net/npm/bootstrap-datepicker@1.10.0/dist/css/bootstrap-datepicker.min.css"  "$vendor\bootstrap-datepicker\css\bootstrap-datepicker.min.css"
Download "https://cdn.jsdelivr.net/npm/bootstrap-datepicker@1.10.0/dist/js/bootstrap-datepicker.min.js"    "$vendor\bootstrap-datepicker\js\bootstrap-datepicker.min.js"

Write-Host "`n=== DataTables ===" -ForegroundColor Yellow
Download "https://cdn.datatables.net/1.13.8/css/jquery.dataTables.min.css"  "$vendor\datatables\css\jquery.dataTables.min.css"
Download "https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js"    "$vendor\datatables\js\jquery.dataTables.min.js"
$dtImages = @("sort_asc.png","sort_desc.png","sort_both.png","sort_asc_disabled.png","sort_desc_disabled.png")
foreach ($img in $dtImages) {
    Download "https://cdn.datatables.net/1.13.8/images/$img"  "$vendor\datatables\images\$img"
}

Write-Host "`n=== SweetAlert2 ===" -ForegroundColor Yellow
Download "https://cdn.jsdelivr.net/npm/sweetalert2@11/dist/sweetalert2.all.min.js"  "$vendor\sweetalert2\sweetalert2.all.min.js"

Write-Host "`n=== Quill ===" -ForegroundColor Yellow
Download "https://cdn.jsdelivr.net/npm/quill@2.0.2/dist/quill.snow.css"  "$vendor\quill\quill.snow.css"

Write-Host "`n=== html5shiv & respond.js (IE legacy) ===" -ForegroundColor Yellow
Download "https://cdn.jsdelivr.net/npm/html5shiv@3.7.3/dist/html5shiv.min.js"     "$vendor\html5shiv\html5shiv.js"
Download "https://cdn.jsdelivr.net/npm/respond.js@1.4.2/dest/respond.min.js"      "$vendor\respond\respond.min.js"

Write-Host "`n=== Google Fonts Roboto (local) ===" -ForegroundColor Yellow
$robotoFonts = @(
    @{w=300; style="normal"; file="roboto-v32-latin-300.woff2";     url="https://fonts.gstatic.com/s/roboto/v32/KFOlCnqEu92Fr1MmSU5fBBc4AMP6lQ.woff2"},
    @{w=400; style="normal"; file="roboto-v32-latin-regular.woff2"; url="https://fonts.gstatic.com/s/roboto/v32/KFOmCnqEu92Fr1Mu4mxKKTU1Kg.woff2"}
)
foreach ($r in $robotoFonts) {
    Download $r.url "$vendor\fonts\roboto\$($r.file)"
}
$robotoCss = @"
@font-face {
  font-family: 'Roboto';
  font-style: normal;
  font-weight: 300;
  font-display: swap;
  src: url('../fonts/roboto/roboto-v32-latin-300.woff2') format('woff2');
}
@font-face {
  font-family: 'Roboto';
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url('../fonts/roboto/roboto-v32-latin-regular.woff2') format('woff2');
}
"@
$robotoDir = "$vendor\fonts"
if (-not (Test-Path $robotoDir)) { New-Item -ItemType Directory -Path $robotoDir -Force | Out-Null }
Set-Content "$vendor\fonts\roboto.css" $robotoCss -NoNewline

Write-Host "`n=== CKEditor 4.17.2 ===" -ForegroundColor Yellow
$ckEditorFiles = @(
    "ckeditor.js",
    "config.js",
    "contents.css",
    "styles.js",
    "skins/moono-lisa/editor.css",
    "skins/moono-lisa/editor_gecko.css",
    "skins/moono-lisa/icons.png",
    "skins/moono-lisa/icons_hidpi.png"
)
foreach ($f in $ckEditorFiles) {
    $dest = "$vendor\ckeditor\$($f -replace '/', '\')"
    Download "https://cdn.ckeditor.com/4.17.2/standard/$f"  $dest
}

Write-Host "`nDone! All vendor files downloaded to $vendor" -ForegroundColor Green
