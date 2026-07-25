[CmdletBinding()]
param(
    [ValidateRange(1, 100)]
    [int]$Boards = 4,
    [ValidateSet("Build", "LabStock")]
    [string]$Profile = "Build",
    [string]$BaseBom = "output/fabrication/unit-board-revA/unit-board-jlcpcb-bom.csv",
    [string]$OutputDirectory = "output/fabrication/unit-board-revA"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$baseBomPath = if ([IO.Path]::IsPathRooted($BaseBom)) {
    $BaseBom
} else {
    Join-Path $repositoryRoot $BaseBom
}
$outputPath = if ([IO.Path]::IsPathRooted($OutputDirectory)) {
    $OutputDirectory
} else {
    Join-Path $repositoryRoot $OutputDirectory
}

if (-not (Test-Path -LiteralPath $baseBomPath)) {
    throw "Base BOM not found: $baseBomPath"
}
New-Item -ItemType Directory -Path $outputPath -Force | Out-Null

$parts = @(
    [pscustomobject]@{ Refs="C1,C2,C5,C6,C7,C8,C9,C13,C15,C17,C18,C201,C203"; Value="100nF 50V X7R 10%"; Footprint="0603"; Manufacturer="KEMET"; Mpn="C0603C104K5RACTU"; DigiKey="399-C0603C104K5RACTUCT-ND"; Category="Passive"; Owned=0; Note="MCU, CAN, LDO, VDDA and NRST decoupling" }
    [pscustomobject]@{ Refs="C3,C4"; Value="10pF 50V C0G 5%"; Footprint="0603"; Manufacturer="Samsung Electro-Mechanics"; Mpn="CL10C100JB8NNNC"; DigiKey="1276-1027-1-ND"; Category="Passive"; Owned=0; Note="HSE load capacitors; do not substitute X7R" }
    [pscustomobject]@{ Refs="C10"; Value="4.7uF 25V X7R 10%"; Footprint="0805"; Manufacturer="Murata Electronics"; Mpn="GRM21BZ71E475KE15K"; DigiKey="490-GRM21BZ71E475KE15KCT-ND"; Category="Passive"; Owned=0; Note="3V3 bulk" }
    [pscustomobject]@{ Refs="C11,C14"; Value="1uF 25V X7R 10%"; Footprint="0603"; Manufacturer="Taiyo Yuden"; Mpn="TMK107B7105KA-T"; DigiKey="587-2984-1-ND"; Category="Passive"; Owned=0; Note="VDDA and VREF+ local bulk" }
    [pscustomobject]@{ Refs="C12"; Value="10nF 50V C0G 5%"; Footprint="0603"; Manufacturer="TDK"; Mpn="CGA3E2NP01H103J080AA"; DigiKey="445-12383-1-ND"; Category="Passive"; Owned=0; Note="VREF+; C0G required" }
    [pscustomobject]@{ Refs="C16"; Value="10nF 100V X7R 10%"; Footprint="0603"; Manufacturer="Murata Electronics"; Mpn="GRM188R72A103KA01D"; DigiKey="490-GRM188R72A103KA01DCT-ND"; Category="Passive"; Owned=0; Note="5V ADC monitor filter" }
    [pscustomobject]@{ Refs="C101"; Value="2.2uF 25V X7R 10%"; Footprint="0805"; Manufacturer="Murata Electronics"; Mpn="GCM21BR71E225KA73L"; DigiKey="490-4787-1-ND"; Category="Passive"; Owned=0; Note="LM66100 VIN" }
    [pscustomobject]@{ Refs="C202,C204"; Value="10uF 10V X7R 10%"; Footprint="0805"; Manufacturer="TDK"; Mpn="C2012X7R1A106K125AC"; DigiKey="445-6857-1-ND"; Category="Passive"; Owned=0; Note="TLV1117LV input/output; verify DC-bias effective capacitance" }
    [pscustomobject]@{ Refs="R1"; Value="120R 1% 0.1W"; Footprint="0603"; Manufacturer="YAGEO"; Mpn="RC0603FR-07120RL"; DigiKey="311-120HRCT-ND"; Category="Passive"; Owned=0; Note="CAN termination" }
    [pscustomobject]@{ Refs="R2,R3,R15,R16,R17,R18"; Value="0R jumper 0.1W"; Footprint="0603"; Manufacturer="YAGEO"; Mpn="RC0603JR-070RL"; DigiKey="311-0.0GRCT-ND"; Category="Passive"; Owned=0; Note="VREF/HSE/SPI configurable links" }
    [pscustomobject]@{ Refs="R4"; Value="10k 1% 0.1W"; Footprint="0603"; Manufacturer="YAGEO"; Mpn="RC0603FR-0710KL"; DigiKey="311-10.0KHRCT-ND"; Category="Passive"; Owned=0; Note="BOOT0 pull-down" }
    [pscustomobject]@{ Refs="R13"; Value="33k 1% 0.1W"; Footprint="0603"; Manufacturer="YAGEO"; Mpn="RC0603FR-0733KL"; DigiKey="311-33.0KHRCT-ND"; Category="Passive"; Owned=0; Note="5V monitor divider high side" }
    [pscustomobject]@{ Refs="R14"; Value="22k 1% 0.1W"; Footprint="0603"; Manufacturer="YAGEO"; Mpn="RC0603FR-0722KL"; DigiKey="311-22.0KHRCT-ND"; Category="Passive"; Owned=0; Note="5V monitor divider low side" }
    [pscustomobject]@{ Refs="R19,R20,R21,R22"; Value="1k 1% 0.1W"; Footprint="0603"; Manufacturer="YAGEO"; Mpn="RC0603FR-071KL"; DigiKey="311-1.00KHRCT-ND"; Category="Passive"; Owned=0; Note="LED current limiting" }
    [pscustomobject]@{ Refs="FB1"; Value="600R at 100MHz 500mA"; Footprint="0603"; Manufacturer="Murata Electronics"; Mpn="BLM18AG601SN1D"; DigiKey="490-1014-1-ND"; Category="Passive"; Owned=0; Note="VDDA ferrite bead" }
    [pscustomobject]@{ Refs="D1,D2"; Value="ESD2CAN24-Q1"; Footprint="SOT-23"; Manufacturer="Texas Instruments"; Mpn="ESD2CAN24DBZRQ1"; DigiKey="296-ESD2CAN24DBZRQ1CT-ND"; Category="Semiconductor"; Owned=0; Note="CAN ESD protection" }
    [pscustomobject]@{ Refs="D6,D8"; Value="Green LED"; Footprint="0603"; Manufacturer="Lite-On"; Mpn="LTST-C190KGKT"; DigiKey="160-1435-1-ND"; Category="Semiconductor"; Owned=0; Note="PWR and RUN LEDs" }
    [pscustomobject]@{ Refs="D7"; Value="BAT54S dual Schottky"; Footprint="SOT-23"; Manufacturer="onsemi"; Mpn="BAT54SLT1G"; DigiKey="BAT54SLT1GOSCT-ND"; Category="Semiconductor"; Owned=0; Note="ADC clamp" }
    [pscustomobject]@{ Refs="D9"; Value="Yellow LED"; Footprint="0603"; Manufacturer="Lite-On"; Mpn="LTST-C190KSKT"; DigiKey="160-1437-1-ND"; Category="Semiconductor"; Owned=0; Note="COMM LED" }
    [pscustomobject]@{ Refs="D10"; Value="Red LED"; Footprint="0603"; Manufacturer="Lite-On"; Mpn="LTST-C190KRKT"; DigiKey="160-1436-1-ND"; Category="Semiconductor"; Owned=0; Note="ERR LED" }
    [pscustomobject]@{ Refs="J1"; Value="JST GH 2-position right-angle"; Footprint="JST GH 1.25mm"; Manufacturer="JST"; Mpn="SM02B-GHS-TB"; DigiKey="455-1564-1-ND"; Category="Connector"; Owned=0; Note="5V input" }
    [pscustomobject]@{ Refs="J2,J3,J4,J5"; Value="JST GH 3-position right-angle"; Footprint="JST GH 1.25mm"; Manufacturer="JST"; Mpn="SM03B-GHS-TB"; DigiKey="455-SM03B-GHS-TBCT-ND"; Category="Connector"; Owned=0; Note="Central and C620 CAN" }
    [pscustomobject]@{ Refs="J6"; Value="JST GH 6-position right-angle"; Footprint="JST GH 1.25mm"; Manufacturer="JST"; Mpn="SM06B-GHS-TB"; DigiKey="455-1568-1-ND"; Category="Connector"; Owned=0; Note="AMT22" }
    [pscustomobject]@{ Refs="J7"; Value="JST GH 6-position vertical"; Footprint="JST GH 1.25mm"; Manufacturer="JST"; Mpn="BM06B-GHS-TBT"; DigiKey="455-BM06B-GHS-TBTCT-ND"; Category="Connector"; Owned=0; Note="SWD/debug" }
    [pscustomobject]@{ Refs="SW1"; Value="SPDT slide switch"; Footprint="JS series custom"; Manufacturer="C&K (Littelfuse)"; Mpn="JS102011SAQN"; DigiKey="401-1999-1-ND"; Category="Switch"; Owned=0; Note="CAN termination enable" }
    [pscustomobject]@{ Refs="SW3"; Value="3-position DIP switch"; Footprint="SMD 3-pole DIP"; Manufacturer="OMRON"; Mpn="A6S-3104-H"; DigiKey="39-A6S-3104-H-ND"; Category="Switch"; Owned=0; Note="Unit ID" }
    [pscustomobject]@{ Refs="U1"; Value="Ideal diode 1.5A"; Footprint="SC-70-6"; Manufacturer="Texas Instruments"; Mpn="LM66100DCKR"; DigiKey="296-53541-1-ND"; Category="IC"; Owned=0; Note="Reverse polarity/current protection" }
    [pscustomobject]@{ Refs="U2"; Value="3.3V LDO"; Footprint="SOT-223"; Manufacturer="Texas Instruments"; Mpn="TLV1117LV33DCYR"; DigiKey="296-28778-1-ND"; Category="IC"; Owned=0; Note="3.3V regulator" }
    [pscustomobject]@{ Refs="U3,U5"; Value="CAN transceiver with VIO"; Footprint="SOIC-8"; Manufacturer="Texas Instruments"; Mpn="TCAN1051VDRQ1"; DigiKey="296-44228-1-ND"; Category="IC"; Owned=0; Note="Central and C620 CAN" }
    [pscustomobject]@{ Refs="U4"; Value="STM32G474 512KB"; Footprint="LQFP-64 10x10 P0.5"; Manufacturer="STMicroelectronics"; Mpn="STM32G474RET6"; DigiKey="497-STM32G474RET6-ND"; Category="IC"; Owned=10; Note="Already purchased project stock" }
    [pscustomobject]@{ Refs="Y1"; Value="8MHz 8pF crystal"; Footprint="3225 4-pad"; Manufacturer="ECS Inc."; Mpn="ECS-80-8-33Q-JES-TR"; DigiKey="50-ECS-80-8-33Q-JES-TRCT-ND"; Category="Crystal"; Owned=0; Note="HSE" }
)

$baseRefs = @(
    Import-Csv -LiteralPath $baseBomPath |
        ForEach-Object { $_.Designator -split "," } |
        ForEach-Object { $_.Trim() } |
        Where-Object { $_ } |
        Sort-Object -Unique
)
$mappedRefs = @(
    $parts |
        ForEach-Object { $_.Refs -split "," } |
        ForEach-Object { $_.Trim() } |
        Where-Object { $_ }
)
$duplicateRefs = @($mappedRefs | Group-Object | Where-Object Count -gt 1)
$mappedUnique = @($mappedRefs | Sort-Object -Unique)
$missingRefs = @($baseRefs | Where-Object { $_ -notin $mappedUnique })
$extraRefs = @($mappedUnique | Where-Object { $_ -notin $baseRefs })

if ($duplicateRefs -or $missingRefs -or $extraRefs) {
    throw "Procurement map mismatch. Duplicates=$($duplicateRefs.Name -join ',') Missing=$($missingRefs -join ',') Extra=$($extraRefs -join ',')"
}

$labStockMinimums = @{
    "C1,C2,C5,C6,C7,C8,C9,C13,C15,C17,C18,C201,C203" = 100
    "C3,C4" = 25
    "C10" = 20
    "C11,C14" = 25
    "C12" = 25
    "C16" = 25
    "C101" = 20
    "C202,C204" = 25
    "R1" = 25
    "R2,R3,R15,R16,R17,R18" = 100
    "R4" = 50
    "R13" = 50
    "R14" = 50
    "R19,R20,R21,R22" = 100
    "FB1" = 20
    "D1,D2" = 20
    "D6,D8" = 25
    "D7" = 20
    "D9" = 20
    "D10" = 20
    "J1" = 10
    "J2,J3,J4,J5" = 30
    "J6" = 10
    "J7" = 10
    "SW1" = 10
    "SW3" = 10
    "U1" = 10
    "U2" = 10
    "U3,U5" = 12
    "U4" = 10
    "Y1" = 10
}

$plan = foreach ($part in $parts) {
    $quantityPerBoard = @($part.Refs -split ",").Count
    $requiredQuantity = $quantityPerBoard * $Boards
    $targetQuantity = if ($part.Category -eq "Passive") {
        $withAttrition = [Math]::Max([Math]::Ceiling($requiredQuantity * 1.2), $requiredQuantity + 2)
        [int]([Math]::Ceiling($withAttrition / 5.0) * 5)
    } else {
        $requiredQuantity + 1
    }
    if ($Profile -eq "LabStock") {
        $targetQuantity = [Math]::Max($targetQuantity, [int]$labStockMinimums[$part.Refs])
    }
    $orderQuantity = [Math]::Max(0, $targetQuantity - [int]$part.Owned)

    [pscustomobject]@{
        "Customer Reference" = $part.Refs
        "Value / Description" = $part.Value
        "Footprint" = $part.Footprint
        "Manufacturer" = $part.Manufacturer
        "Manufacturer Part Number" = $part.Mpn
        "DigiKey Part Number" = $part.DigiKey
        "Qty Per Board" = $quantityPerBoard
        "Boards" = $Boards
        "Required Quantity" = $requiredQuantity
        "Target Qty With Spares" = $targetQuantity
        "Owned Quantity" = [int]$part.Owned
        "Order Quantity" = $orderQuantity
        "Notes" = $part.Note
    }
}

$nameSuffix = if ($Profile -eq "LabStock") { "${Boards}boards-plus-stock" } else { "${Boards}boards" }
$planFile = Join-Path $outputPath "unit-board-procurement-plan-${nameSuffix}.csv"
$digiKeyFile = Join-Path $outputPath "unit-board-digikey-bom-${nameSuffix}.csv"

$plan | Export-Csv -LiteralPath $planFile -NoTypeInformation -Encoding utf8NoBOM
$plan |
    Where-Object { $_."Order Quantity" -gt 0 } |
    Select-Object `
        "DigiKey Part Number",
        @{ Name="Quantity"; Expression={ $_."Order Quantity" } },
        "Manufacturer",
        "Manufacturer Part Number",
        "Customer Reference",
        @{ Name="Description"; Expression={ $_."Value / Description" } } |
    Export-Csv -LiteralPath $digiKeyFile -NoTypeInformation -Encoding utf8NoBOM

Write-Host "DigiKey procurement BOM created for $Boards boards ($Profile profile):"
Write-Host "  $planFile"
Write-Host "  $digiKeyFile"
