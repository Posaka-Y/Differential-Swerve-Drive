(kicad_sch
	(version 20260306)
	(generator "eeschema")
	(generator_version "10.0")
	(uuid "cdb60579-f192-43a7-86d7-10cb974d2bc4")
	(paper "A4")
	(title_block
		(title "Teensy 4.1 Central Board - Module Index")
		(date "2026-08-04")
		(rev "A - HUMAN REVIEW DRAFT")
		(company "Differential Swerve")
		(comment 1 "Responsibility-based hierarchical schematic")
		(comment 2 "Global labels connect modules")
	)
	(lib_symbols)
	(text "Open each child sheet and review its inputs, outputs, protection and TBD gates independently."
		(exclude_from_sim no)
		(at 17.78 22.86 0)
		(effects
			(font
				(size 1.27 1.27)
				(thickness 0.254)
				(bold yes)
			)
			(justify left bottom)
		)
		(uuid "04babcc2-f131-4f33-a583-1995547156d4")
	)
	(text "PCB gate: replace pin-explicit generic IC symbols, close every TBD, save as current .kicad_sch, then reach ERC 0."
		(exclude_from_sim no)
		(at 22.86 153.67 0)
		(effects
			(font
				(size 1.397 1.397)
				(thickness 0.2794)
				(bold yes)
			)
			(justify left bottom)
		)
		(uuid "0e6c03cb-63ab-4a1e-abf1-df347fc8b39a")
	)
	(text "Cross-module nets use global labels: +5V_SYS, +5V_TEENSY, +3V3_TEENSY, GND_CTRL, CANx_TX/RX, safety and I2C signals."
		(exclude_from_sim no)
		(at 22.86 147.32 0)
		(effects
			(font
				(size 1.397 1.397)
				(thickness 0.2794)
				(bold yes)
			)
			(justify left bottom)
		)
		(uuid "29eba12c-9e9b-4af3-9783-93baa636ad6b")
	)
	(text "CENTRAL BOARD RESPONSIBILITY MAP"
		(exclude_from_sim no)
		(at 17.78 16.51 0)
		(effects
			(font
				(size 2.286 2.286)
				(thickness 0.4572)
				(bold yes)
			)
			(justify left bottom)
		)
		(uuid "7cc0ae20-9958-47a3-b3a2-c17a2bb6f012")
	)
	(sheet
		(at 22.86 33.02)
		(size 71.12 35.56)
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(dnp no)
		(fields_autoplaced yes)
		(stroke
			(width 0)
			(type solid)
		)
		(fill
			(color 0 0 0 0)
		)
		(uuid "00000000-0000-0000-0000-000000007001")
		(property "Sheetname" "Power Input and 5V Distribution"
			(at 22.86 32.1814 0)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.524 1.524)
				)
				(justify left bottom)
			)
		)
		(property "Sheetfile" "modules/100-power.sch"
			(at 22.86 69.1646 0)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left top)
			)
		)
		(instances
			(project "central-board"
				(path "/cdb60579-f192-43a7-86d7-10cb974d2bc4"
					(page "2")
				)
			)
		)
	)
	(sheet
		(at 111.76 33.02)
		(size 71.12 35.56)
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(dnp no)
		(fields_autoplaced yes)
		(stroke
			(width 0)
			(type solid)
		)
		(fill
			(color 0 0 0 0)
		)
		(uuid "00000000-0000-0000-0000-000000007002")
		(property "Sheetname" "Teensy 4.1 Carrier and Safety GPIO"
			(at 111.76 32.1814 0)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.524 1.524)
				)
				(justify left bottom)
			)
		)
		(property "Sheetfile" "modules/200-teensy.sch"
			(at 111.76 69.1646 0)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left top)
			)
		)
		(instances
			(project "central-board"
				(path "/cdb60579-f192-43a7-86d7-10cb974d2bc4"
					(page "4")
				)
			)
		)
	)
	(sheet
		(at 200.66 33.02)
		(size 71.12 35.56)
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(dnp no)
		(fields_autoplaced yes)
		(stroke
			(width 0)
			(type solid)
		)
		(fill
			(color 0 0 0 0)
		)
		(uuid "00000000-0000-0000-0000-000000007003")
		(property "Sheetname" "CAN Communication"
			(at 200.66 32.1814 0)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.524 1.524)
				)
				(justify left bottom)
			)
		)
		(property "Sheetfile" "modules/300-can.sch"
			(at 200.66 69.1646 0)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left top)
			)
		)
		(instances
			(project "central-board"
				(path "/cdb60579-f192-43a7-86d7-10cb974d2bc4"
					(page "6")
				)
			)
		)
	)
	(sheet
		(at 22.86 91.44)
		(size 71.12 35.56)
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(dnp no)
		(fields_autoplaced yes)
		(stroke
			(width 0)
			(type solid)
		)
		(fill
			(color 0 0 0 0)
		)
		(uuid "00000000-0000-0000-0000-000000007004")
		(property "Sheetname" "E-stop and Contactor Safety"
			(at 22.86 90.6014 0)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.524 1.524)
				)
				(justify left bottom)
			)
		)
		(property "Sheetfile" "modules/600-safety.sch"
			(at 22.86 127.5846 0)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left top)
			)
		)
		(instances
			(project "central-board"
				(path "/cdb60579-f192-43a7-86d7-10cb974d2bc4"
					(page "3")
				)
			)
		)
	)
	(sheet
		(at 111.76 91.44)
		(size 71.12 35.56)
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(dnp no)
		(fields_autoplaced yes)
		(stroke
			(width 0)
			(type solid)
		)
		(fill
			(color 0 0 0 0)
		)
		(uuid "00000000-0000-0000-0000-000000007005")
		(property "Sheetname" "Battery and Motor Power Monitoring (page 5)"
			(at 111.76 90.6014 0)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.524 1.524)
				)
				(justify left bottom)
			)
		)
		(property "Sheetfile" "modules/700-monitoring.sch"
			(at 111.76 127.5846 0)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left top)
			)
		)
		(instances
			(project "central-board"
				(path "/cdb60579-f192-43a7-86d7-10cb974d2bc4"
					(page "5")
				)
			)
		)
	)
	(sheet
		(at 200.66 91.44)
		(size 71.12 35.56)
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(dnp no)
		(fields_autoplaced yes)
		(stroke
			(width 0)
			(type solid)
		)
		(fill
			(color 0 0 0 0)
		)
		(uuid "00000000-0000-0000-0000-000000007006")
		(property "Sheetname" "Expansion and Test Access"
			(at 200.66 90.6014 0)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.524 1.524)
				)
				(justify left bottom)
			)
		)
		(property "Sheetfile" "modules/800-expansion.sch"
			(at 200.66 127.5846 0)
			(show_name no)
			(do_not_autoplace no)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left top)
			)
		)
		(instances
			(project "central-board"
				(path "/cdb60579-f192-43a7-86d7-10cb974d2bc4"
					(page "7")
				)
			)
		)
	)
	(sheet_instances
		(path "/"
			(page "1")
		)
	)
	(embedded_fonts no)
)
