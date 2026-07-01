BeforeAll {
    $strRepositoryRoot = Split-Path -Path (Split-Path -Path $PSScriptRoot -Parent) -Parent
    . (Join-Path -Path $strRepositoryRoot -ChildPath 'src/tools/Resolve-PSScriptAnalyzerCandidate.ps1')

    function Initialize-CandidateTestRepository {
        # .SYNOPSIS
        # Creates a temporary repository-like directory for candidate tests.
        #
        # .DESCRIPTION
        # Creates a unique directory under the system temporary directory. Tests
        # use this helper so filesystem fixtures are isolated and easy to clean
        # up after each test case.
        #
        # .EXAMPLE
        # $strRoot = Initialize-CandidateTestRepository
        #
        # # Returns a unique temporary directory path.
        #
        # .INPUTS
        # None. This function does not accept pipeline input.
        #
        # .OUTPUTS
        # [string] The temporary repository root path.
        #
        # .NOTES
        # PRIVATE/INTERNAL HELPER - This function is not part of the public
        # API surface. Parameters, return shape, and positional contract may
        # change without notice.
        #
        # Version: 1.0.20260701.0
        # Positional parameters are not supported.
        #
        [CmdletBinding(PositionalBinding = $false)]
        [OutputType([string])]
        param()

        Set-StrictMode -Version Latest

        $strRoot = [System.IO.Path]::Combine(
            [System.IO.Path]::GetTempPath(),
            ('pssa-candidate-{0}' -f [System.Guid]::NewGuid().ToString('N'))
        )
        [void]([System.IO.Directory]::CreateDirectory($strRoot))
        return $strRoot
    }

    function Add-CandidateTestFile {
        # .SYNOPSIS
        # Adds a UTF-8 test file beneath a temporary repository root.
        #
        # .DESCRIPTION
        # Creates parent directories as needed and writes a small PowerShell
        # source file using an explicit UTF-8 encoding.
        #
        # .PARAMETER RepositoryRoot
        # The temporary repository root.
        #
        # .PARAMETER RepositoryRelativePath
        # The repository-relative file path to create.
        #
        # .EXAMPLE
        # Add-CandidateTestFile -RepositoryRoot $strRoot -RepositoryRelativePath 'src/a.ps1'
        #
        # # Creates src/a.ps1 under the repository root.
        #
        # .INPUTS
        # None. This function does not accept pipeline input.
        #
        # .OUTPUTS
        # None.
        #
        # .NOTES
        # PRIVATE/INTERNAL HELPER - This function is not part of the public
        # API surface. Parameters, return shape, and positional contract may
        # change without notice.
        #
        # Version: 1.0.20260701.0
        # Positional parameters are not supported.
        #
        [CmdletBinding(PositionalBinding = $false)]
        [OutputType([void])]
        param(
            [Parameter(Mandatory = $true)]
            [ValidateNotNullOrEmpty()]
            [string]$RepositoryRoot,

            [Parameter(Mandatory = $true)]
            [ValidateNotNullOrEmpty()]
            [string]$RepositoryRelativePath
        )

        Set-StrictMode -Version Latest

        $strFullPath = [System.IO.Path]::Combine($RepositoryRoot, $RepositoryRelativePath)
        $strParentDirectory = [System.IO.Path]::GetDirectoryName($strFullPath)
        [void]([System.IO.Directory]::CreateDirectory($strParentDirectory))
        $objEncoding = [System.Text.UTF8Encoding]::new($false)
        [System.IO.File]::WriteAllText($strFullPath, "Write-Output 'test'`n", $objEncoding)
    }
}

Describe "Resolve-PSScriptAnalyzerCandidate" {
    It "Selects bracket-containing paths and escapes analyzer input literally" {
        # Arrange
        $strRoot = Initialize-CandidateTestRepository
        try {
            $strRelativePath = 'src/Invoke-[Build].ps1'
            Add-CandidateTestFile -RepositoryRoot $strRoot -RepositoryRelativePath $strRelativePath
            $strFullPath = Resolve-PSScriptAnalyzerFullPath -RepositoryRoot $strRoot -Path $strRelativePath

            # Act
            $objCandidate = Resolve-PSScriptAnalyzerCandidate `
                -RepositoryRoot $strRoot `
                -CandidatePath $strRelativePath `
                -RepositoryRelativePath $strRelativePath

            # Assert
            $objCandidate.OutcomeCategory | Should -Be 'selected'
            $objCandidate.RepositoryRelativePath | Should -Be $strRelativePath
            $objCandidate.EscapedAnalyzerPath | Should -Be (
                [System.Management.Automation.WildcardPattern]::Escape($strFullPath)
            )
        } finally {
            Remove-Item -LiteralPath $strRoot -Recurse -Force
        }
    }

    It "Excludes exact node_modules segments without excluding substrings" {
        # Arrange
        $strRoot = Initialize-CandidateTestRepository
        try {
            $strExcludedPath = 'node_modules/.bin/tool.ps1'
            $strSelectedPath = 'tools/node_modules_helper/Build.ps1'
            Add-CandidateTestFile -RepositoryRoot $strRoot -RepositoryRelativePath $strExcludedPath
            Add-CandidateTestFile -RepositoryRoot $strRoot -RepositoryRelativePath $strSelectedPath

            # Act
            $objExcludedCandidate = Resolve-PSScriptAnalyzerCandidate `
                -RepositoryRoot $strRoot `
                -CandidatePath $strExcludedPath `
                -RepositoryRelativePath $strExcludedPath
            $objSelectedCandidate = Resolve-PSScriptAnalyzerCandidate `
                -RepositoryRoot $strRoot `
                -CandidatePath $strSelectedPath `
                -RepositoryRelativePath $strSelectedPath

            # Assert
            $objExcludedCandidate.OutcomeCategory | Should -Be 'policy-excluded'
            $objExcludedCandidate.ReasonCode | Should -Be 'NodeModulesSegment'
            $objSelectedCandidate.OutcomeCategory | Should -Be 'selected'
        } finally {
            Remove-Item -LiteralPath $strRoot -Recurse -Force
        }
    }

    It "Preserves CRLF in structured records while rendering summaries on one line" {
        # Arrange
        $strRelativePath = "src/line`r`nbreak.ps1"
        $objCandidate = ConvertTo-PSScriptAnalyzerCandidateRecord `
            -CandidateFullName "/repo/$strRelativePath" `
            -RepositoryRelativePath $strRelativePath `
            -OutcomeCategory 'unsafe' `
            -ReasonCode 'MissingTarget'

        # Act
        $objSummary = Get-PSScriptAnalyzerCandidateSummary -Candidate @($objCandidate)
        $arrSummaryLine = @(ConvertTo-PSScriptAnalyzerCandidateSummaryLine -CandidateSummary $objSummary)

        # Assert
        $objSummary.Unsafe | Should -Not -BeNullOrEmpty
        $objSummary.Unsafe[0].RepositoryRelativePath | Should -Be $strRelativePath
        ($arrSummaryLine -join "`n") | Should -Match 'src/line\\r\\nbreak\.ps1'
        foreach ($strLine in $arrSummaryLine) {
            $strLine.Contains("`r") | Should -BeFalse
            $strLine.Contains("`n") | Should -BeFalse
        }
    }

    It "Classifies leaf reparse candidates that escape the repository as unsafe" {
        # Arrange
        $strRoot = Initialize-CandidateTestRepository
        $strExternalRoot = Initialize-CandidateTestRepository
        try {
            Add-CandidateTestFile -RepositoryRoot $strExternalRoot -RepositoryRelativePath 'outside.ps1'
            $strLinkPath = [System.IO.Path]::Combine($strRoot, 'link.ps1')
            $strTargetPath = [System.IO.Path]::Combine($strExternalRoot, 'outside.ps1')

            try {
                [void](New-Item -Path $strLinkPath -ItemType SymbolicLink -Target $strTargetPath -ErrorAction Stop)
            } catch {
                Set-ItResult -Skipped -Because 'Filesystem or current privileges do not allow symlink creation.'
                return
            }

            # Act
            $objCandidate = Resolve-PSScriptAnalyzerCandidate `
                -RepositoryRoot $strRoot `
                -CandidatePath 'link.ps1' `
                -RepositoryRelativePath 'link.ps1'

            # Assert
            $objCandidate.OutcomeCategory | Should -Be 'unsafe'
            $objCandidate.ReasonCode | Should -BeIn @(
                'TargetOutsideRepository',
                'ReparsePointResolutionUnsupported'
            )
        } finally {
            Remove-Item -LiteralPath $strRoot -Recurse -Force
            Remove-Item -LiteralPath $strExternalRoot -Recurse -Force
        }
    }
}
