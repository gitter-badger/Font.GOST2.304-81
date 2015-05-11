#!/usr/bin/python
# -*- coding: utf-8 -*-

import fontforge, psMat
import sys, os, re

def copyGlyphs ( font, sourceGlyphs, newGlyphs = None, transform = psMat.identity(), suffix = '' ) :
	for i, sourceGlyphName in enumerate( sourceGlyphs ):
		sourceGlyph = font[ sourceGlyphName ]
		newGlyphUnicode = -1
		newGlyphName = ''
		if newGlyphs:
			newGlyphItem = newGlyphs[i]
			if type( newGlyphItem ) is tuple:
				newGlyphUnicode = newGlyphItem[0]
				newGlyphName = newGlyphItem[1]
				newGlyphId = newGlyphName
			else:
				if type( newGlyphItem ) is str:
					newGlyphName = newGlyphItem
					newGlyphId = newGlyphName
				else:
					if type( newGlyphItem ) is int:
						newGlyphUnicode = newGlyphItem
						newGlyphId = newGlyphUnicode
		else:
			newGlyphName = sourceGlyph.glyphname + suffix
			newGlyphId = newGlyphName
		if newGlyphId not in font:
			newGlyph = font.createChar( newGlyphUnicode, newGlyphName )
			if suffix:
				newGlyph.glyphname = sourceGlyph.glyphname + suffix
			else:
				newGlyph.glyphname = newGlyphName
			newGlyph.width = sourceGlyph.width
			newGlyph.addReference( sourceGlyph.glyphname )
			newGlyph.transform( transform )
	# to-do: copy kern data


toolsdir = os.path.dirname(os.path.abspath(sys.argv[0])) + '/'
sourcefile = sys.argv[1]
sourceFeaturesFile = sys.argv[2]
destfile = sys.argv[3]
version = sys.argv[4]

font = fontforge.open (sourcefile)

for glyph in font.glyphs():
#	if not ( glyph.background.isEmpty() ):
		glyph.layers[1] += glyph.background
		glyph.layerrefs[1] += glyph.layerrefs[0]
		glyph.layers[0] = fontforge.layer()

font.is_quadratic = False

# set font version
font.version = version
ver = re.search('^(?P<major>\d+)\.(?P<minor>\d+)(\.(?P<release>\d+)(\.(?P<build>\d+))?)?', version)
if ver is not None:
	font.sfntRevision = None
	for name in font.sfnt_names:
		if name[1] == 'Version':
			font.appendSFNTName (name[0], name[1], '')
	font.appendSFNTName ( 'English (US)', 'Version', font.version )

font.encoding = 'unicode'

# additional glyphs for marks
for markData in [
	[0x0300, 0x0060, 0x02CB] # grave
	, [0x0301, 0x00B4, 0x02CA] # acute
	, [0x0302, 0x005E, 0x02C6] # circumflex
	, [0x0303, 0x007E, 0x02DC] # tilde
	, [0x0304, 0x00AF, 0x02C9] # macron
	, [0x0306, 0x02D8] # breve
	, [0x0307, 0x02D9] # dot above
	, [0x0308, 0x00A8] # diaeresis
	, [0x030A, 0x02DA] # ring above
	, [0x030B, 0x02DD] # double acute
	, [0x030C, 0x02C7] # caron
	, [0x030D, 0x02C8] # vertical line above
	, [0x0312, 0x02BB] # turned comma above
	, [0x0313, 0x02BC] # comma above
	, [0x0314, 0x02BD] # reversed comma above
	, [0x0328, 0x02DB] # ogonek
	, [0x0332, 0x005F] # low line
	, [0x0333, 0x2017] # double low line
	]:
	if markData[0] in font:
		sourceGlyph = font[markData[0]]
		for i in range(1, len(markData)):
			if markData[i] not in font:
				markGlyph = font.createMappedChar ( markData[i] )
				markGlyph.width =  font.strokewidth + sourceGlyph.width - sourceGlyph.right_side_bearing - sourceGlyph.left_side_bearing
				markGlyph.addReference ( sourceGlyph.glyphname, psMat.translate( font.strokewidth / 2 - sourceGlyph.left_side_bearing, 0 ) )

# add 0-9, +-=() subscript, superscript
subscriptScale = 10.0/14
subscriptTransform = psMat.compose ( psMat.scale(subscriptScale), psMat.translate(0, -500) )
subToSuperscriptTransform = psMat.translate(0, 1400)
sourceUnicode = range(0x30, 0x3A) + [0x002B, 0x2212, 0x003D, 0x0028, 0x0029]
subUnicode = range(0x2080, 0x208F)
superUnicode = [0x2070, 0x00B9, 0x00B2, 0x00B3] + range( 0x2074, 0x207F )
copyGlyphs( font, sourceUnicode + [ 'zero.slash', 'three.alt' ], subUnicode + [ -1, -1 ], subscriptTransform, suffix = '.sub' )
copyGlyphs( font, subUnicode + [ 'zero.slash.sub', 'three.alt.sub' ],
	[ ( code, font[ sourceUnicode[i] ].glyphname + '.sup' ) for i, code in enumerate( superUnicode ) ] + [ 'zero.slash.sup', 'three.alt.sup' ],
	subToSuperscriptTransform )

digitsNames = [ font[ code ].glyphname for code in range(0x30, 0x3A) ]
allDigitsNames = digitsNames + [ 'three.alt', 'zero.slash' ]
copyGlyphs( font, [ name + '.sub' for name in allDigitsNames ], [ name + '.dnom' for name in allDigitsNames ], psMat.translate(0, 500) )
copyGlyphs( font, [ name + '.sup' for name in allDigitsNames ], [ name + '.numr' for name in allDigitsNames ] )

# build roman digits
if 0x2160 not in font:
	font.selection.select ( ['ranges', 'unicode'], 0x2160, 0x216F )
	font.build()

font.mergeFeature (sourceFeaturesFile)

font.save (destfile)
