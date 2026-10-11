# Original DOCX full structural audit at candidate4641743

Audit scope: original 147210288-byte DOCX, immutable SHA256 b253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5, repository head4641743a6da1086be75649a5e34c896283842888. No repository edits, no original changes, no publication. Original SHA256 before and after matches; ZIP CRC traversal reports no corrupt member.

## Structural fidelity actually established

- Independently traversed all16 XML parts using lxml, separately from production ElementTree reader. Inventory includes main document,2headers,footnotes/endnotes and metadata/styles/theme/settings/customXML.
- Reader returns14684logical units:14678 main+6auxiliary.1802paragraphs,12826table cells,11unsupported-body units,41equations,4empty-note units.
- All18305 native w:t source nodes accounted for by source-ordinal mapping.14639 non-equation/nonempty units have exact native text prefixes independently reconstructed from source XML,0mismatches/0missing source text nodes. Includes header1=34w:t,header2=62w:t;auxiliary note XML contains no w:t. This is source-content completeness,not rendered-order/physical-placement verification.
- All41 source OMML nodes/298m:t tokens preserved in41reader equation units. Independent comparison of full expanded XML tags,attributes,text,child order and internal tails finds0missing/extra structures (root tail excluded intentionally). Does not evaluate notation or prove mathematical/engineering meaning. No native OMML exists in auxiliary parts of this original.
-642media assets retained in source_assets:138EMF,369PNG,115JPEG,9JPG,11WDP.683candidates=41OMML+138EMF+504other media. Every candidate retrieved via actual _docx_payload matches its declared payload hash and source hash (0identity failures). Native OMML candidate serialization is normalized ElementTree,not original byte-identical XML.
-671supported blip/VML graphic references independently match671reader-bound refs,0missing/extra within that supported scope,0unavailable descriptors/0media hash mismatches. Drawing source inventory main655drawing/5pict/21object/649inline/6anchor;headers each1drawing/1pict/1anchor.
- All138uniqueEMF binaries independently traversed:28449records,3357EMR_EXTTEXTOUTW records. All literal Unicode text,record offsets,code-unit counts and options match reader descriptors,0mismatches.149EMF reference occurrences repeat3394text records. Other unsupported text-record types83/96/97/108 count0 in this source.120bitmap payload descriptorsAVAILABLE;bitmap/GDI transformations are not applied.

## Explicit missing representation or verification scope

-11WDP image-layer refs are PRESENT in source as a14:imgLayer r:embed under a:blip extensions,NOT unreferenced assets. Production bind_images only binds a:blip and v:imagedata;these11advanced image-layer bindings/processing are absent from reader locators although all11payloads remain in source_assets. Total supported+WDP graphic references682 versus671reader refs.
-21embedded OLE/PBrush objects/binaries exist under word/embeddings;these are preserved in original but excluded from source_assets and _docx_payload candidate path and not semantically decoded by reader. Their graphic previews are separately bound. This prevents claimingALL embedded content ingestion.
- Current source_assets/_docx_payload only enumerate OMML in word/document.xml. Real original has no auxiliary OMML,so no actual formula is lost here;documents with header/footer/note equations would have a coverage gap.
-19EMFs include COMMENT_CONTENT_NOT_READ. All138 retain GRAPHICS_NOT_RENDERED,FONT_MAPPING_UNVERIFIED,TEXT_PLACEMENT_UNVERIFIED;120alsoBITMAP_PAYLOADS_UNTRANSFORMED. Source bytes preserve records but do not prove their content/meaning was read.
- Reader limitations remain:PHYSICAL_PAGES_UNKNOWN,LAYOUT_NOT_VERIFIED,EMBEDDED_CONTENT_NOT_READ,AUXILIARY_PLACEMENT_UNVERIFIED;69unitsFIELD_NOT_EVALUATED,6300unitsMERGED_CELL_UNVERIFIED,allgraphic transforms/content and equation interpretations unverified.
- Word docProps cached Pages=491 is metadata only,not an independently validated physical page count. XML source ordinals and declared grid positions are not actual page/table placement.

## Local visual rendering capability

Actual packaged LibreOfficeDev26.8.0.0.alpha0 and Inkscape1.2.2 available without installing anything. Canonical document skill render_docx.py launched on unchanged original with isolated profile,output_dir stage13-docx-audit/render and emit_pdf;see render.log. Completion/all-page visual review is not yet established at this report snapshot. Standalone representative EMF exported to sample-emf.png with Inkscape exit0 and visually inspected: plan blocks,grid labels and visible outline geometry render. This demonstrates local EMF rasterization capability,not full138asset correctness or Word placement.

Fontconfig capability probe (font-render-capability.json) resolves declared Cambria Math to Latin Modern Math,Calibri to DejaVu Sans,Times New Roman to Nimbus Roman,ISOCPEUR/GOST type A/Wingdings to DejaVu Sans in the current environment. These are actual font substitutions from fc-match,not proof of the exact final LibreOffice font selection,which must be inspected in its rendered output. They are an explicit obstacle to claiming exact source-font/layout equivalence without further verification.

Exact visual formula/EMF/layout fidelity cannot be closed by hash identity or XML parity. It requires complete successful original rendering,inspection of every page/formula/graphic,source-to-page traceability (including alternative content,image layers,OLE previews,anchors,crops,font mapping),and an authoritative original Word rendering/reference when exact source-layout equivalence is required. Qualified engineering acceptance remains separately blocked until those representations/meanings and governing evidence are reviewed. This structural audit does not grant verified=true,ENGINEER ACCEPTED or FINAL_AUDIT.

## Evidence files

summary.json;xml-part-inventory.json;native-text-nodes.json;ordinal-native-text-audit.json;reader-units.json;independent-formula-inventory.json;formula-full-xml-structure-audit.json;independent-media-inventory.json;candidate-payload-identities.json;independent-graphics-reference-inventory.json;all-image-ole-relationships.json;wdp-reference-inventory.json;hdphoto-ole-node-inventory.json;independent-emf-record-audit.json;sample.emf;sample-emf.png;emf-render.log;render.log. Reproduction scripts audit.py,ordinal_audit.py,formula_structure.py,emf_independent.py.
