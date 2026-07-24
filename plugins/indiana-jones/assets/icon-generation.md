# Indiana Jones plugin icon

The active icon is a close pixel-touched portrait of an original fictional
archaeologist on a transparent background. His cognac fedora preserves the
earlier hat identity, while a rugged beard and gold-reflective glasses capture
the focused instant before a discovery.

## Generation workflow

1. Generate the isolated explorer portrait on a flat `#00ff00` chroma-key field
   with the built-in image-generation tool.
2. Remove the key with the image-generation skill's helper, using automatic
   border sampling, soft matte, despill, and one-pixel edge contraction.
3. Resize with nearest-neighbor filtering to a 512 by 512 RGBA PNG so the
   stepped pixel treatment remains crisp.
4. Check transparent corners, the alpha bounds, chroma fringe, and legibility
   at 64 by 64 and 32 by 32.
5. Reference `logo-v12.png` from both `interface.logo` and
   `interface.composerIcon` in `.codex-plugin/plugin.json`.

## Active gold-reflection explorer prompt

Hat and pixel reference: `logo-v11.png`

Pixel-language reference:
`/Users/anon/Desktop/Screenshot 2026-07-24 at 12.48.39.png`

```text
Use case: style-transfer and background-extraction
Asset type: transparent square Codex skill icon, readable at 16–32 px
Input images: Image 1 preserves the pixel-touched cognac fedora, its pinched crown, broad brim, dark band, stepped silhouette, and quantized highlights. Image 2 supplies only the friendly Codex-pet pixel language: crisp block clusters, restrained dark edge definition, simplified readable forms, and small-size clarity. Do not copy the mascot, body, pose, blue palette, or number.
Primary request: create a tight head-and-hat portrait of one original fictional archaeological explorer at the charged instant before a discovery. Keep the result archetypal: no Harrison Ford likeness, no direct Indiana Jones face, and no identifiable real person.
Subject: rugged adult explorer with a warm complexion, weathered cheeks, a full short-to-medium dark-brown beard with a few muted copper or gray pixels, and the cognac fedora from Image 1. Add refined dark-brown round-aviator glasses. The smoky amber lenses are the emotional focal point, reflecting bold asymmetrical metallic-gold light as if a newly opened chamber is illuminating him. Do not depict a readable treasure or artifact in the lenses.
Expression: quiet awe, intense focus, and contained excitement. Keep the mouth mostly hidden by the beard and set in a calm determined line. No caricature, aggression, or broad smile.
Composition: extremely close near-front three-quarter portrait. Fedora and face fill about 84–88 percent of the square. Show the complete crown, enough brim to remain iconic, both lenses, nose, beard, and chin, with only a hint of neck or collar. Preserve a compact almost-circular silhouette and add a small transparent safety margin around the complete subject.
Style: premium hybrid of a smooth 3D software avatar and lightly pixelated Codex-mascot sprite. Use deliberate two-to-four-pixel stepped contours, chunky but nuanced beard clusters, simplified skin planes, quantized shadow bands, crisp reflective-lens pixels, and restrained dark edge definition. Dimensional and handsome rather than a full retro 8-bit portrait.
Lighting and palette: concentrate warm discovery light in the glasses with subtle amber bounce on cheekbones, nose, beard tips, and the hat underside. Use cognac, chestnut, dark chocolate, warm skin, deep umber beard, smoky amber lenses, and concentrated metallic-gold highlights.
Background: perfectly uniform flat solid #00ff00 for local transparency extraction. No gradient, checkerboard, noise, shadow, glow, vignette, floor, reflection, or green inside the character.
Constraints: exactly one original explorer portrait; no actor likeness, second person, room, landscape, treasure, artifact, bag, magnifying glass, shovel, trowel, map, book, weapon, whip, logo, badge, text, number, initials, watermark, or extra props.
Post-process: remove the chroma field with automatic border sampling, soft matte, despill, and one-pixel alpha contraction. Scale the cutout to 92 percent on the transparent canvas for a safety margin, resize to 512 by 512 with nearest-neighbor filtering, and validate transparent corners plus 64- and 32-pixel previews.
```

## Previous pixel-touched fedora prompt

Content reference: `logo-v7.png`

Pixel-language reference:
`/Users/anon/Desktop/Screenshot 2026-07-24 at 12.48.39.png`

```text
Use case: background-extraction and style-transfer
Asset type: transparent square Codex skill icon, readable at 16–32 px
Input images: Image 1 supplies only the archaeology fedora identity: warm cognac or chestnut color, iconic pinched crown, broad gently curved brim, dark chocolate band, and dimensional shading. Image 2 supplies only the subtle pixel-art language: crisp stepped silhouette edges, small block-shaped color clusters, restrained dark edge definition, and compact software-icon readability. Do not copy the mascot, face, body, blue palette, or number.
Subject: exactly one fedora hat and nothing else. Present it upright in a clean near-front three-quarter view, centered, immediately recognizable, and fully inside the canvas. Fill about 78–82 percent of the square with balanced padding.
Style: polished hybrid of smooth 3D app icon and lightly pixelated Codex-mascot sprite. Keep the large forms rounded and dimensional, but quantize the silhouette into deliberate two-to-four-pixel steps and describe highlights and shadows with crisp pixel clusters rather than continuous photoreal gradients. The pixel treatment is subtle and premium, not an 8-bit parody.
Hat: preserve a strong asymmetrical pinched crown, broad brim, and one simple dark band. Use warm cognac crown and brim, dark chocolate band, small amber highlights, and deep umber shadow pixels. Use a restrained dark-brown one-pixel-style edge only where it improves small-size readability.
Background: perfectly uniform flat solid #00ff00 for local alpha extraction. No checkerboard, gradient, noise, shadow, glow, halo, vignette, or green inside the hat.
Constraints: no buckle, feathers, stitching, scratches, map lines, room, floor, tile, circle, bag, magnifying glass, shovel, trowel, map, book, character, face, body, text, number, logo, watermark, or additional object.
Post-process: remove the chroma field with automatic border sampling, soft matte, despill, and one-pixel alpha contraction. Resize to 512 by 512 with nearest-neighbor filtering and validate transparent corners plus 64- and 32-pixel previews.
```

## Previous isometric contour-room prompt

Content and material reference: `logo-v7.png`

Architecture reference:
`/Users/anon/Desktop/8b99b7b8-42a2-4c16-9785-b35f7b0d98c1.jpeg`

```text
Use case: style-transfer
Asset type: full-bleed square Codex plugin icon, readable at 32–64 px
Input images: Image 1 is the current archaeology icon and preserves the warm fedora, dimensional leather satchel, premium smooth 3D materials, bevels, ambient occlusion, soft studio lighting, and compact object scale. Image 2 supplies only the room architecture and camera logic.
Primary request: rebuild the archaeology icon as a true orthographic isometric three-plane interior. The room has one flat left wall, one flat right wall, and one flat floor meeting at a centered rear vertical corner, with softly rounded concave fillets at the wall-floor and wall-wall seams. Keep all three main surfaces planar.
Map language: replace Image 2's square grid with sparse warm taupe and terracotta topographic contour lines printed or microscopically embossed across all three planes. Continue the lines coherently through the rounded seams so the room reads simultaneously as an isometric space and a map. The contour lines must not deform the planar room.
Foreground subjects: exactly three archaeological research objects arranged as a strong balanced triangle: fedora at upper center, field-research satchel at lower-left, and magnifying glass at lower-right.
Hat: compact warm cognac felt fedora with a confident silhouette, dark chocolate band, crisp crown and brim, controlled highlights, and a soft contact shadow.
Bag: substantial warm ochre or cognac leather satchel with a projecting flap, visible side gussets, darker right and lower planes, one central dark strap, a compact brass buckle, rounded bevel highlights, and strong ambient occlusion. No loose strap or belt crossing the scene.
Magnifying glass: elegant circular brass rim, optically clear slightly smoky lens, and short dark walnut handle angled down-right. The lens subtly and convincingly enlarges one contour line beneath it without surreal distortion.
Composition: preserve clean negative-space channels between the three objects while keeping their combined silhouette compact. Ground every object with coherent contact shadows. Prioritize hat first, bag second, and magnifying glass third.
Camera and architecture: orthographic isometric three-quarter view with a centered rear corner and clearly legible left wall, right wall, and floor. No perspective distortion.
Style and lighting: premium smooth 3D app-icon rendering, clean silhouettes, physically plausible soft shading, precise bevels, restrained ambient occlusion, one large soft key from upper-left, warm neutral fill, and controlled highlights.
Canvas: full opaque square artwork edge-to-edge. No exterior margin, floating rounded tile, transparent corners, green field, or chroma background; the host applies its own corner mask.
Constraints: no bowl, pit, excavation trench, carved topography, terraced basin, stepped elevation, rock ledges, raised relief, curving terrain walls, shovel, trowel, loose map, paper sheet, book, character, person, face, text, letters, logo, watermark, or extra props.
Avoid: square grid, rainbow sheet, flat bag shading, fuzzy fabric, photoreal clutter, muddy brown-on-brown separation, distorted lens, crowded collage, and weak room geometry.
```

## Previous full-bleed relief-map prompt

Content reference: `logo-v6.png`

Style references are the same three files listed in the rounded-tile section.

```text
Use case: style-transfer
Asset type: full-bleed square Codex plugin icon, readable at 32–64 px
Input images: Image 1 is the current archaeology icon and content/style continuity reference. Images 2–4 are app-icon style references for isometric space, smooth geometry, polished shading, and icon-scale restraint.
Primary request: create the next archaeology icon concept as a full-bleed smooth 3D app icon. Turn the isometric background itself into the map: replace the drawn rectangular grid with a sculpted topographic map language. Remove the foreground paper map entirely and replace it with one compact archaeology trowel. Keep the hat and field satchel.
Full canvas: the artwork fills the entire square edge-to-edge. No floating rounded tile, no green field, no transparent corners, no white exterior margin, no empty outer canvas, and no separate icon object sitting inside a larger image. Render an opaque complete square icon; allow the host UI to apply its own corner mask.
Isometric map environment: build a shallow, softly rounded isometric cartographic chamber across the full canvas, with a floor plane and two gently rising rear planes. Instead of a square construction grid, cover the surfaces with elegant topographic contour curves and subtle stepped elevation forms. The contour language must wrap coherently across the floor and rear planes, reading simultaneously as a map and as an isometric spatial level. Use sparse terracotta/taupe contour lines, soft relief, and warm ivory stone/paper materials. No latitude-longitude grid, graph-paper grid, square tiles, or checkerboard.
Foreground subjects: exactly three simplified objects: one expedition fedora, one closed archaeology field satchel, and one compact hand trowel. No paper map, map book, scroll, or loose sheet—the map is fully represented by the environment.
Hat: smooth sculpted caramel/chestnut fedora with a strong pinched crown, broad curved brim, and dark chocolate band. Satin molded surface with controlled highlights and clean form gradients, matching the polished app-icon language.
Bag: make the satchel the shading showcase. Use a structured ochre/golden-tan body with a clearly projecting rounded flap, visible side gusset depth, a darker lower/right plane, one centered dark-brown strap, and one compact brass buckle. Add precise bevel highlights, rich midtone gradients, and soft ambient occlusion in the flap seam, buckle recess, and contact area. It should feel dimensional and premium, not like a flat orange blob. No shoulder strap, loose belt, or tiny stitching.
Trowel: one short archaeology hand trowel with a clean triangular satin-steel blade and compact dark walnut/brown handle. Simplify it into bold geometric volumes. Place it at lower-right on a diagonal, blade pointing gently toward the center, with a restrained metallic highlight and soft edge bevel. It should read as an excavation tool, not a garden spade, weapon, or giant shovel.
Composition: arrange the object centers as a compact triangular cluster within the full isometric map environment: hat at upper center, bag at lower-left, trowel at lower-right. Use controlled overlap and contact shadows so the group feels grounded in the map level. Preserve generous breathing room between object silhouettes but no unused exterior margin. The background contour flow should subtly lead the eye around the three objects.
Camera: consistent orthographic three-quarter view; shallow isometric depth; no perspective distortion; strong icon-scale geometry
Style/medium: high-end smooth 3D app-icon rendering; vector-clean forms with physically plausible soft shading; satin ceramic/rubber/metal material response; precise bevels, luminous gradients, and restrained ambient occlusion; polished and minimal like the references, without copying their specific subjects
Lighting: one large soft key from upper-left, neutral-warm fill, stronger dimensional shading than Image 1, coherent contact shadows on the map surface, controlled highlights with no harsh glare
Color palette: warm ivory and pale stone map environment, sparse terracotta/taupe contour lines, caramel/chestnut hat, ochre satchel, dark chocolate accents, muted brass buckle, satin warm-gray steel blade, dark walnut handle. No rainbow colors.
Hierarchy: hat first, bag second, trowel third, isometric contour-map environment as the unifying fourth layer. Maintain clear tonal separation at 32 px.
Constraints: exactly one hat, one closed satchel, and one trowel; no paper map or book; no character, mascot, person, face, body, limbs, celebrity likeness, whip, firearm, compass, shovel with long handle, glasses, puzzle piece, notebook, scrolls, ruins, text, letters, initials, logo, watermark, outer border, floating rounded tile, green background, transparency, or additional props.
Avoid: visible rectangular grid; graph paper; map sheet behind objects; transparent padding; blank exterior margin; flat bag shading; fuzzy fabric; photoreal leather grain; excessive stitching; crowded collage; giant tool; dark black background; cartoon outlines; low-detail clay blobs.
```

## Rounded-tile style-transfer prompt

Style references:

- `/Users/anon/Desktop/8b99b7b8-42a2-4c16-9785-b35f7b0d98c1.jpeg`
- `/Users/anon/Desktop/d114eb93-fed2-4345-bcd2-34a0d2e1bffa.jpeg`
- `/Users/anon/Desktop/3b8da387-8181-4931-9651-d66e24128b81.jpeg`

Content reference: `logo-v5.png`

```text
Use case: style-transfer
Asset type: premium square Codex plugin icon, readable at 32–64 px
Input images: Images 1–3 are style references only. Image 4 is the content and identity reference for the three archaeology objects.
Primary request: reinterpret the fedora, field satchel, and separate folded map from Image 4 in the refined app-icon language of Images 1–3: minimal geometric 3D forms, smooth molded materials, crisp bevels, controlled gradients, soft ambient depth, precise silhouettes, and elegant negative space. Do not copy the subject or layout of any style reference.
Canvas/background: place the icon on one centered rounded-square tile occupying about 84 percent of the canvas, with a generous 20–22 percent corner radius. Outside the rounded tile, use a perfectly flat solid #00ff00 chroma-key field for later removal. The green must be uniform and must not appear inside the tile or objects. No shadow may extend from the tile onto the green field.
Tile: a softly dimensional warm ivory-to-pale-stone rounded square, clean and understated, with a shallow inset studio-alcove feel and subtle corner curvature. Use very faint warm-gray construction/grid lines on the interior surfaces only, inspired by Image 1, but keep them sparse and subordinate. The tile itself should feel like a polished modern macOS/iOS app icon rather than a literal room.
Subjects: exactly three simplified archaeology objects: one sculpted expedition fedora, one closed field-research satchel, and one separate partially unfolded map. Preserve their recognizability from Image 4 while reducing surface realism and tiny detail.
Hat: smooth caramel-to-chestnut molded 3D form with a clean pinched crown, broad curved brim, and one dark chocolate band. No felt fibers, stitching, scratches, or photoreal texture. Use a few soft highlights and form gradients to describe the volume.
Satchel: compact rounded rectangular ochre/tan 3D block with a clean flap, one centered dark-brown strap, and one simple brass geometric buckle. Remove the shoulder strap entirely for clarity. No loose belt, side loops, seams, canvas weave, or tiny stitching.
Map: one independent warm-white geometric sheet, roughly square and only partly open into two broad panels with one central fold. Give it a subtle paper thickness, one slightly lifted corner, and three or four sparse terracotta contour curves. It must look like one clean folded map—not a fan, accordion, scroll, brochure, book, stack, or paper emerging from the bag.
Composition: arrange the object centers as a compact triangle within an imaginary circle: hat at upper center, satchel at lower-left, map at lower-right. Use slight controlled overlap toward the middle so the group reads as one emblem, while every object remains separate and instantly legible. The combined silhouette should be balanced and almost circular. Keep all three comfortably within the rounded tile with generous internal padding.
Camera: consistent orthographic three-quarter view with shallow depth; no perspective distortion; strong icon-scale geometry
Style/medium: high-end smooth 3D app-icon rendering; vector-clean shapes with physically plausible soft shading; satin ceramic/rubber/plastic material response; subtle bevels and ambient occlusion; luminous but restrained; no grain, noise, brushwork, or plush/clay texture
Lighting: one large soft key from upper-left, gentle neutral fill, soft internal contact shadows between overlapping objects only; polished highlights with no harsh glare
Color palette: warm ivory tile, caramel/chestnut hat, ochre satchel, dark chocolate accents, small muted brass buckle, warm-white map, restrained terracotta contour lines. No rainbow colors. Do not use green anywhere inside the tile or objects.
Hierarchy: hat first, satchel second, map third. Simplify aggressively enough that the icon remains clean at 32 px.
Constraints: exactly one hat, one closed satchel, and one separate two-panel map; no character, mascot, person, face, body, limbs, celebrity likeness, whip, weapons, compass, shovel, glasses, puzzle piece, notebook, scrolls, ruins, text, letters, initials, logo, watermark, outer border, visible circle, pedestal, realistic environment, or additional props. Keep the rounded tile fully visible and centered.
Avoid: copying the rainbow ribbon, envelope, pen, or notebook subjects from the references; photoreal leather or fabric; fuzzy textures; crowded collage; tangled strap; map inside bag; accordion map; excessive folds; brown-on-brown muddiness; flat 2D illustration; cartoon outlines; dark black background; green spill.
```

## High-fidelity field-map prompt

```text
Use case: logo-brand
Asset type: premium square Codex skill/plugin icon, readable at 32–64 px
Input images: Image 1 is a high-fidelity style, palette, lighting, and material-quality reference only. Generate a fresh composition rather than iteratively editing the existing collage.
Primary request: create a polished 3D-rendered archaeologist emblem using exactly three objects: one expedition fedora, one closed field-research satchel, and one separate partially unfolded rectangular field map. Recover the rich material quality and dimensionality of Image 1 while improving the arrangement and replacing the strange fan-shaped map.
Scene/backdrop: perfectly flat solid #00ff00 chroma-key background for later background removal
Map shape: one natural field map made from a single roughly square cream parchment sheet, about 4:3 in proportion. It is only partly unfolded, with one broad central valley fold and one subtle horizontal crease, creating two large readable panels rather than many accordion panels. One outer corner curls very slightly. The map has a clean irregular rectangular silhouette, a few broad muted-rust topographic contour lines, and no writing. It must not look like a fan, brochure, pleated screen, ribbon, scroll, book, or stack of papers.
Arrangement: compose the three object centers as a compact triangle inside an imaginary circle. Place the fedora at the upper-left/top vertex, the satchel at the lower-left/bottom vertex, and the separate map at the right vertex. Pull the forms inward so they lightly overlap near the center and read as one cohesive emblem, while every object remains unmistakable. The hat brim may pass slightly in front of the inner top edge of the bag and the inner corner of the map. The map may sit a little behind those central edges, but it remains visibly independent and is never inserted into or emerging from the bag. The combined outside contour should be nearly circular, with balanced visual weight and even padding.
Hat: richly rendered weathered chestnut felt fedora with a clean center crease, front pinch, gently irregular brim, and dark leather band. Show a refined three-quarter view with tactile felt nap and controlled edge definition.
Satchel: compact warm tan-canvas archaeology field bag with softly worn dark-umber leather trim, closed flap, one simple front buckle, and minimal oversized stitching. Any shoulder strap is shortened and tucked behind the bag as one logical attached arc following only the lower-left outer contour. No foreground loop or loose buckle.
Style/medium: premium stylized 3D object rendering, halfway between soft clay icon and high-end tactile product visualization; smooth rounded forms, crisp silhouettes, nuanced felt/canvas/leather/parchment microtexture, realistic material response without photoreal clutter. Match the dimensional quality and warm polish of Image 1, not the flatter or over-patterned look of later revisions.
Camera/composition: consistent three-quarter camera angle and perspective across all objects; compact centered group fills about 78 percent of the square; elegant asymmetry; clean negative-space channels; strong legibility at 32 px
Lighting/mood: one coherent soft studio key light with subtle warm fill on all objects, quietly adventurous and scholarly; controlled highlights and natural form shading on objects only; no cast shadow or contact shadow on the background
Color palette: brand brown near #8A5A2B, chestnut felt, dark umber leather, warm tan canvas, cream parchment, muted rust contour lines. Do not use green anywhere in the objects.
Hierarchy: hat first, bag second, map third. Preserve enough tonal contrast that all three remain separate after icon reduction.
Constraints: exactly one hat, one closed satchel, and one separate single-sheet map; no creature, mascot, face, body, limbs, human, celebrity likeness, whip, weapons, notebook, scrolls, tools, compass, glasses, puzzle pieces, ruins, text, initials, badges, logos, watermark, border, visible circle, frame, pedestal, floor plane, or environmental scene. The #00ff00 background must be perfectly uniform with no gradient, texture, reflection, lighting variation, green spill, or shadow. Crisp clean outer edges for chroma-key removal.
Avoid: accordion or fan map; map sticking out of bag; map rolled up; many paper panels; catalogue spacing; disconnected floating collage; tangled strap; belt circling all objects; detached buckle; flat illustration; low-detail clay blobs; excessive surface pattern; glossy plastic; sepia wash; photoreal product clutter.
```

## Compact-circle refinement prompt

```text
Use case: precise-object-edit
Asset type: square Codex skill/plugin icon, readable at 32–64 px
Input images: Image 1 is the edit target
Primary request: change only the spacing, scale, and rotation of the existing three objects so they become one compact circular emblem instead of an airy catalogue layout. Preserve the exact hat, closed satchel, separate folded map, materials, colors, lighting, and flat green background from Image 1.
Composition change: keep the hat at the top vertex, satchel at lower-left, and separate map at lower-right, but pull all three objects inward by roughly 25 percent. Move the hat downward so the lower edge of its brim slightly overlaps the inner top corners of both lower objects. Rotate the satchel a few degrees toward the center and rotate the map a few degrees toward the center. Bring the bag and map close enough that their inner corners nearly touch, leaving only a narrow clean negative-space channel. The three object centers still form a balanced triangle, while the combined outside edges trace one strong imaginary circle. The grouping should read as one emblem, fill about 78 percent of the square, and have even padding on every side.
Map invariant: the folded map remains a fully separate object at lower-right. It is not inserted into, attached to, emerging from, or held by the bag. Preserve all visible map folds and sparse contour lines.
Strap invariant: preserve the satchel’s short tidy strap arc entirely behind the bag. No loose foreground strap, crossing belt, detached buckle, or full loop around the composition.
Visual hierarchy: hat first, bag second, map third. Use small controlled overlaps only at the central meeting point; preserve clear object silhouettes and avoid hiding major features.
Constraints: do not add, remove, duplicate, redesign, or restyle any object. Exactly one hat, one closed satchel, and one separate folded map. No creature, mascot, body, face, text, logo, border, visible circle, floor, shadows, or additional props. Preserve the perfectly flat uniform #00ff00 background with crisp clean subject edges.
Avoid: wide empty central gap; disconnected catalogue layout; map inside bag; tangled straps; rectangular outer silhouette; lopsided scale; excessive overlap; floating buckle; new objects.
```

## Triangle layout prompt

```text
Use case: precise-object-edit
Asset type: square Codex skill/plugin icon, readable at 32–64 px
Input images: Image 1 is the edit target and material/style reference
Primary request: refine Image 1 into a more aesthetic, intentional three-object emblem. Keep the fedora, research satchel, and folded contour map, but correct the satchel strap and make the map completely separate from the bag. Arrange the three objects as the vertices of a triangle contained within an imaginary circle.
Scene/backdrop: perfectly flat solid #00ff00 chroma-key background for later background removal
Composition geometry: use an invisible centered circle occupying about 78 percent of the square. Place the fedora at the 12 o’clock/top vertex, the satchel at the 7:30/lower-left vertex, and the separate folded map at the 4:30/lower-right vertex. Each object should have comparable visual weight and its outer silhouette should gently follow the circular boundary. The three objects may overlap slightly toward the center to feel unified, but their identities and edges must remain clear. The overall silhouette should feel circular while the object centers form an equilateral triangle. Keep even breathing room around the entire emblem.
Hat: preserve Image 1’s weathered chestnut fedora, center crease, front pinch, dark leather band, and tactile felt. Show it from a clean three-quarter angle, slightly smaller than in Image 1, centered above the other objects. It must not rest on or hide most of the bag.
Satchel: preserve the warm tan-canvas field bag with dark-umber leather trim and one simple front buckle. Close the flap. Place it independently at lower-left. Correct the shoulder strap: no loose belt crossing the foreground, no detached buckle, no tangled loop. The strap should be a short, tidy arc entirely behind the bag, following only the lower-left edge of the imaginary circle, with both ends visibly and logically attached to the bag.
Map: one separate cream folded survey map at lower-right, resting independently in space and not inserted into, attached to, held by, or emerging from the bag. Show two or three broad accordion folds and a few sparse muted-rust contour lines. Angle it gently toward the center so it balances the hat and bag. Keep a small visible separation from the satchel, or at most a very slight center overlap that never implies the bag contains it.
Style/medium: preserve Image 1’s polished soft 3D clay/felt software-icon treatment, tactile hat nap, simplified canvas weave, softly worn leather, rounded edges, restrained handcrafted detail, and premium friendly warmth. Favor elegant graphic clarity over product realism.
Color palette: brand brown near #8A5A2B, chestnut felt, dark umber leather, warm tan canvas, cream parchment, muted rust contour lines. Do not use green anywhere in the objects.
Lighting/mood: gentle consistent softbox illumination on all three objects, quietly adventurous and scholarly; no cast shadow or contact shadow
Hierarchy: hat first, bag second, map third. Use clean negative-space channels between the three forms. Keep hardware and map marks bold, sparse, and icon-scale.
Invariants: exactly one fedora, one closed satchel, and one separate folded map. Preserve the materials, palette, tactile rendering, and recognizable archaeology theme from Image 1.
Constraints: no creature, mascot, eyes, face, body, limbs, human, celebrity likeness, whip, weapons, notebook, scrolls, tools, compass, glasses, puzzle pieces, ruins, text, initials, badges, logos, watermark, border, visible circle, frame, pedestal, floor plane, environmental scene, loose foreground strap, tangled belt, or floating buckle. The #00ff00 background must be perfectly uniform with no gradient, texture, reflection, lighting variation, green spill, or shadow. Crisp clean outer edges for chroma-key removal.
Avoid: map inside the bag; map emerging from the bag; hat sitting on the bag; disconnected random collage; lopsided visual weight; rectangular overall silhouette; crossing straps; photoreal product photography; busy props; glossy plastic; sepia wash; excessive stitching; visual clutter.
```

## First object-only prompt

```text
Use case: logo-brand
Asset type: square Codex skill/plugin icon, readable at 32–64 px
Input images: Image 1 is a style, palette, and object-material reference only; do not preserve or include its creature
Primary request: create an abstract object-only archaeologist emblem using exactly three recognizable elements from Image 1: the expedition fedora, the field-research satchel, and the folded contour map. Remove the puppet/mascot completely.
Scene/backdrop: perfectly flat solid #00ff00 chroma-key background for later background removal
Subject: a compact sculptural still-life of one weathered chestnut fedora, one sturdy tan-canvas and dark-umber leather research satchel, and one cream folded survey map with a few simple muted-rust contour lines. No living character, body, face, eyes, hands, arms, or feet.
Composition/framing: build a bold triangular emblem. The satchel forms the stable lower-center base at a slight three-quarter angle. The fedora rests naturally across the upper-left portion of the satchel, tilted just enough to reveal its center crease, front pinch, leather band, and iconic brim without hiding the bag. The folded map rises from the partly open bag and unfolds diagonally toward the upper-right, balancing the hat. Let the satchel strap form one clean curved line behind and around the grouping to visually bind the three objects. Strong overlap, compact silhouette, balanced negative space, no floating objects. The grouping fills about 76 percent of the square with generous even padding and remains legible at 32 px.
Style/medium: preserve Image 1’s polished soft 3D clay/felt software-icon treatment, tactile hat nap, simplified canvas weave, softly worn leather, rounded edges, restrained handcrafted detail, and premium friendly warmth; more emblematic and abstract than a realistic product still-life
Color palette: brand brown near #8A5A2B, chestnut felt, dark umber leather, warm tan canvas, cream parchment, muted rust contour lines. Do not use green anywhere in the objects.
Lighting/mood: gentle softbox illumination on the objects only, quietly adventurous and scholarly; controlled highlights; no cast shadow or contact shadow
Hierarchy: hat silhouette first, bag second, map third. Keep the map marks broad and sparse. Keep bag hardware minimal and oversized enough to survive icon reduction.
Constraints: exactly one hat, one satchel, and one folded map; no creature or mascot; no eyes, face, body, limbs, clothing, human, celebrity likeness, whip, weapons, notebook, extra scrolls, tools, compass, glasses, puzzle pieces, ruins, text, initials, badges, logos, watermark, border, frame, pedestal, floor plane, or environmental scene. The #00ff00 background must be perfectly uniform with no gradient, texture, reflection, lighting variation, green spill, or shadow. Crisp clean outer edges for chroma-key removal.
Avoid: direct Indiana Jones or Harrison Ford likeness; movie-poster styling; floating disconnected collage; photoreal product photography; busy props; glossy plastic; sepia wash; excessive tiny stitching; visual clutter.
```

## Creature revision prompt

```text
Use case: precise-object-edit
Asset type: square Codex skill/plugin icon, readable at 32–64 px
Input images: Image 1 is the edit target and identity/style reference
Primary request: keep the same lovable archaeologist creature from Image 1, but redesign the pose and composition so the character feels capable, heroic, and ready to lead an expedition. Make the fedora about 20 percent smaller relative to the creature and add a clearly readable cross-body field-research satchel.
Scene/backdrop: perfectly flat solid #00ff00 chroma-key background for later background removal
Subject and pose: preserve the creature’s exact warm sand-colored clay/plush identity, tiny charcoal dot eyes, rounded proportions, tactile materials, and calm personality. Give it a stronger upright full-body stance: feet planted slightly wider, chest lifted, body turned in a confident three-quarter view, head facing us, one small foot subtly forward. The expression remains minimal but determined through posture and a slightly lowered hat brim. The creature grips the satchel strap near its chest with one hand and holds a small folded survey map at its side with the other.
Hat change: retain the recognizable weathered chestnut expedition fedora with center crease, front pinch, dark leather band, and uneven brim, but scale it down roughly 20 percent. It should fit the head instead of swallowing the character, reveal more forehead/body, and no longer span nearly the whole canvas.
Research bag: add one sturdy cross-body field satchel in dark umber leather and weathered tan canvas. The strap runs clearly across the torso to a bag resting at one hip. The flap is partly open so only two bold research cues are visible: a cream field notebook and one rolled survey sheet. Keep the bag simple and large enough to read as a silhouette at icon size.
Style/medium: preserve Image 1’s polished soft 3D clay/plush software-mascot rendering, warm tactile felt, rounded forms, gentle softbox lighting, and restrained handcrafted detail
Composition/framing: centered full-body three-quarter hero composition with balanced negative space; character fills about 78 percent of the square; hat, eyes, strap, bag, hands, and feet all unobstructed and fully inside frame. Create a clear diagonal from hat crown through shoulder strap to satchel. Prioritize hierarchy: character and posture first, hat second, research bag third, map last.
Color palette: preserve chestnut and brand brown near #8A5A2B, warm sandstone body, dark umber leather, tan canvas, cream paper, and muted rust map line. Do not use green anywhere in the subject.
Lighting/mood: warm, quietly fearless, competent expedition leader; soft controlled illumination on the subject only; no cast shadow or contact shadow
Invariants: keep one creature only; preserve the original mascot identity, dot-face simplicity, materials, palette, and friendly premium-software-pet feel. Keep the result an original archetypal archaeologist, not a human or existing character.
Constraints: no text, initials, badges, logos, watermark, puzzle piece, glasses, whip, weapons, extra tools, ruins, pedestal, floor plane, background scene, dramatic action, or celebrity likeness. The #00ff00 background must be perfectly uniform with no gradients, texture, reflection, lighting variation, green spill, or shadows. Crisp outer edges and generous padding for chroma-key removal.
Avoid: direct Indiana Jones or Harrison Ford likeness; movie-poster styling; oversized hat; timid slouch; seated pose; babyish expression; busy bag contents; photoreal person; glossy plastic; sepia wash; clutter.
```

## Initial generation prompt

```text
Use case: logo-brand
Asset type: square Codex skill/plugin icon, intended to remain readable at 32–64 px
Primary request: create an original tiny archaeologist desktop-companion mascot whose defining silhouette is an oversized brown expedition fedora. Capture the friendly visual grammar of a premium software pet: soft tactile 3D clay/plush rendering, compact rounded body, minimal dot-face expression, gentle personality, exquisite but restrained craftsmanship. Do not copy any existing character or artwork.
Scene/backdrop: perfectly flat solid #00ff00 chroma-key background for later background removal
Subject: one centered, squat, rounded sand-colored mascot peeking from beneath a large weathered chestnut-brown fedora with a classic center crease, front pinch, gently uneven brim, and dark leather band. Two tiny charcoal dot eyes are clearly visible under the brim. The mascot holds one very small folded parchment survey map with a single simple contour-line mark; the map is subordinate to the hat and must not clutter the silhouette. No human face, no celebrity likeness, no whip, no weapons.
Style/medium: polished soft 3D clay/plush icon illustration; rounded forms; subtle felt nap on the hat; simplified materials; warm, playful, intelligent; original software-mascot design
Composition/framing: single subject, centered, near-front three-quarter view, generous even padding, strong silhouette, nearly fills a square while leaving breathing room around the brim; all parts fully in frame
Lighting/mood: gentle softbox-style illumination on the subject only, cozy and curious; controlled highlights; no cast shadow or contact shadow
Color palette: chestnut and brand brown near #8A5A2B, dark umber band, warm sandstone body, cream parchment, tiny muted rust contour line; do not use green anywhere in the subject
Constraints: one mascot only; no text, initials, badge, logo, watermark, border, frame, pedestal, floor plane, environmental scene, glass, puzzle piece, extra props, dramatic action, or photoreal person. The flat #00ff00 background must be one perfectly uniform color with no gradients, texture, reflections, lighting variation, or shadows. Crisp clean outer edges suitable for chroma-key removal. Prioritize small-size icon legibility: hat first, eyes second, map third.
Avoid: direct Indiana Jones/Harrison Ford likeness; movie-poster styling; realistic human anatomy; detailed background; busy accessories; sepia wash; glossy plastic; chibi anime proportions; exaggerated smile; green spill; cast shadow.
```
