Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Create Form
$form = New-Object System.Windows.Forms.Form
$form.Text = "Notepad"
$form.Size = New-Object System.Drawing.Size(600,400)

# Create TextBox
$textbox = New-Object System.Windows.Forms.TextBox
$textbox.Multiline = $true
$textbox.ScrollBars = "Both"
$textbox.Dock = "Fill"
$textbox.Add_TextChanged({
    $charCountLabel.Text = "Characters: " + $textbox.Text.Length.ToString()
    $currentLineLabel.Text = "Line: " + ($textbox.GetLineFromCharIndex($textbox.SelectionStart) + 1).ToString()
    $currentColumnLabel.Text = "Column: " + ($textbox.SelectionStart - $textbox.GetFirstCharIndexOfCurrentLine() + 1).ToString()
})
$form.Controls.Add($textbox)

# Create StatusBar
$statusBar = New-Object System.Windows.Forms.StatusStrip

$charCountLabel = New-Object System.Windows.Forms.ToolStripStatusLabel
$charCountLabel.Text = "Characters: 0"
$statusBar.Items.Add($charCountLabel)

$currentLineLabel = New-Object System.Windows.Forms.ToolStripStatusLabel
$currentLineLabel.Text = "Line: 1"
$statusBar.Items.Add($currentLineLabel)

$currentColumnLabel = New-Object System.Windows.Forms.ToolStripStatusLabel
$currentColumnLabel.Text = "Column: 1"
$statusBar.Items.Add($currentColumnLabel)

$form.Controls.Add($statusBar)

# Create MenuStrip
$menuStrip = New-Object System.Windows.Forms.MenuStrip

# File Menu
$fileMenu = New-Object System.Windows.Forms.ToolStripMenuItem
$fileMenu.Text = "&File"

# New
$newMenuItem = New-Object System.Windows.Forms.ToolStripMenuItem
$newMenuItem.Text = "&New"
$newMenuItem.Add_Click({
    $textbox.Text = ""
})
$fileMenu.DropDownItems.Add($newMenuItem)

# Open
$openMenuItem = New-Object System.Windows.Forms.ToolStripMenuItem
$openMenuItem.Text = "&Open"
$openMenuItem.Add_Click({
    $openFileDialog = New-Object System.Windows.Forms.OpenFileDialog
    $openFileDialog.Filter = "Text Files (*.txt)|*.txt|All Files (*.*)|*.*"
    $openFileDialog.Title = "Open Text File"
    if ($openFileDialog.ShowDialog() -eq "OK") {
        $filePath = $openFileDialog.FileName
        $textbox.Text = Get-Content $filePath
    }
})
$fileMenu.DropDownItems.Add($openMenuItem)

# Save
$saveMenuItem = New-Object System.Windows.Forms.ToolStripMenuItem
$saveMenuItem.Text = "&Save"
$saveMenuItem.Add_Click({
    $saveFileDialog = New-Object System.Windows.Forms.SaveFileDialog
    $saveFileDialog.Filter = "Text Files (*.txt)|*.txt|All Files (*.*)|*.*"
    $saveFileDialog.Title = "Save Text File"
    if ($saveFileDialog.ShowDialog() -eq "OK") {
        $filePath = $saveFileDialog.FileName
        $textbox.Text | Out-File -FilePath $filePath -Force
    }
})
$fileMenu.DropDownItems.Add($saveMenuItem)

# Save As
$saveAsMenuItem = New-Object System.Windows.Forms.ToolStripMenuItem
$saveAsMenuItem.Text = "Save &As"
$saveAsMenuItem.Add_Click({
    $saveFileDialog = New-Object System.Windows.Forms.SaveFileDialog
    $saveFileDialog.Filter = "Text Files (*.txt)|*.txt|All Files (*.*)|*.*"
    $saveFileDialog.Title = "Save Text File As"
    if ($saveFileDialog.ShowDialog() -eq "OK") {
        $filePath = $saveFileDialog.FileName
        $textbox.Text | Out-File -FilePath $filePath -Force
    }
})
$fileMenu.DropDownItems.Add($saveAsMenuItem)

# Exit
$exitMenuItem = New-Object System.Windows.Forms.ToolStripMenuItem
$exitMenuItem.Text = "E&xit"
$exitMenuItem.Add_Click({
    $form.Close()
})
$fileMenu.DropDownItems.Add($exitMenuItem)

$menuStrip.Items.Add($fileMenu)

# Edit Menu
$editMenu = New-Object System.Windows.Forms.ToolStripMenuItem
$editMenu.Text = "&Edit"

# Cut
$cutMenuItem = New-Object System.Windows.Forms.ToolStripMenuItem
$cutMenuItem.Text = "Cu&t"
$cutMenuItem.Add_Click({
    $textbox.Cut()
})
$editMenu.DropDownItems.Add($cutMenuItem)

# Copy
$copyMenuItem = New-Object System.Windows.Forms.ToolStripMenuItem
$copyMenuItem.Text = "&Copy"
$copyMenuItem.Add_Click({
    $textbox.Copy()
})
$editMenu.DropDownItems.Add($copyMenuItem)

# Paste
$pasteMenuItem = New-Object System.Windows.Forms.ToolStripMenuItem
$pasteMenuItem.Text = "&Paste"
$pasteMenuItem.Add_Click({
    $textbox.Paste()
})
$editMenu.DropDownItems.Add($pasteMenuItem)

# Select All
$selectAllMenuItem = New-Object System.Windows.Forms.ToolStripMenuItem
$selectAllMenuItem.Text = "&Select All"
$selectAllMenuItem.Add_Click({
    $textbox.SelectAll()
})
$editMenu.DropDownItems.Add($selectAllMenuItem)

$menuStrip.Items.Add($editMenu)


# Theme Menu
$themeMenu = New-Object System.Windows.Forms.ToolStripMenuItem
$themeMenu.Text = "&Theme"

# Light Theme
$lightThemeMenuItem = New-Object System.Windows.Forms.ToolStripMenuItem
$lightThemeMenuItem.Text = "&Light Theme"
$lightThemeMenuItem.Add_Click({
    $form.BackColor = [System.Drawing.Color]::White
    $form.ForeColor = [System.Drawing.Color]::Black
    $menuStrip.BackColor = [System.Drawing.Color]::White
    $menuStrip.ForeColor = [System.Drawing.Color]::Black
    $statusBar.BackColor = [System.Drawing.Color]::White
    $statusBar.ForeColor = [System.Drawing.Color]::Black
})
$themeMenu.DropDownItems.Add($lightThemeMenuItem)

# Dark Theme
$darkThemeMenuItem = New-Object System.Windows.Forms.ToolStripMenuItem
$darkThemeMenuItem.Text = "&Dark Theme"
$darkThemeMenuItem.Add_Click({
    $form.BackColor = [System.Drawing.Color]::Black
    $form.ForeColor = [System.Drawing.Color]::White
    $menuStrip.BackColor = [System.Drawing.Color]::Black
    $menuStrip.ForeColor = [System.Drawing.Color]::White
    $statusBar.BackColor = [System.Drawing.Color]::Black
    $statusBar.ForeColor = [System.Drawing.Color]::White
})
$themeMenu.DropDownItems.Add($darkThemeMenuItem)

$menuStrip.Items.Add($themeMenu)

# Print Menu
$printMenu = New-Object System.Windows.Forms.ToolStripMenuItem
$printMenu.Text = "&Print"

# Print
$printMenuItem = New-Object System.Windows.Forms.ToolStripMenuItem
$printMenuItem.Text = "&Print"
$printMenuItem.Add_Click({
    $printDialog = New-Object System.Windows.Forms.PrintDialog
    if ($printDialog.ShowDialog() -eq "OK") {
        $printDocument = New-Object System.Drawing.Printing.PrintDocument
        $printDocument.DocumentName = "Print Document"
        $printDocument.PrintPage.Add({
            $text = $textbox.Text
            $textStartPosition = [System.Drawing.PointF]::new(100, 100)
            $e.Graphics.DrawString($text, $textbox.Font, [System.Drawing.Brushes]::Black, $textStartPosition)
        })
        $printDocument.Print()
    }
})
$printMenu.DropDownItems.Add($printMenuItem)

$menuStrip.Items.Add($printMenu)

$form.Controls.Add($menuStrip)

# Run Form
$form.ShowDialog()
