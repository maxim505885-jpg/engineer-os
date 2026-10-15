# Passive OLE source bitmap decoder

Implementation ownership: only engineering/local_app/ole_bitmap.py and tests/test_ole_bitmap.py. No commit/push; no changes to office.py,word_images.py,UI or requirements by this agent. Parent performs integration. Baseline9e253567a3eaa2fbc024a1a05fd960da5e4206ac,branchfeat/docx-layer-ole-coverage-20261011.

## API

- describe(data): small boundedJSON descriptor,statusAVAILABLE orUNAVAILABLE,sourceOLE bytes/sha256,stream_count,total_stream_bytes,bitmaps[],content_verified=false,layout_verified=false.
- extract(data,stream=None): exact raw BMP/DIB bytes for validated logicalstreambitmapspan;does not change original source.
- render(data,stream=None): derivedPNGbytes via boundedPillowImage.frombytes BI_RGB decoding. NoOLEactivation,noGDI/macros,subprocesses,externalpaths,network orsemanticinterpretation.
- stream selector: exactrootstreamstring orlist/tupleofpathcomponents. DefaultNone requires exactly1availablebitmap,otherwiseValueError. Bitmap descriptors supplystream[],stream_bytes,stream_sha256,bitmap_offset,bitmap_bytes,bitmap_sha256,bits_offset/bits_bytes,stride,dimensions,bitdepth,format. All offsets areLOGICAL_STREAM_BYTES,not physicalCFB offsets. OriginalcompleteOLE hash isdescriptor.sha256.

## Actual original21-object results

Original DOCX147210288bytes,SHA256before=after=b253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5.21word/embeddings/*.bin compoundfiles all parsedwithoutolefileissues.

ALL21 contain root \x01Ole10Native stream,notCONTENTS. Structure:u32NativeDataSize exactlylen(stream)-4,thenBMPsignatureatstreamoffset4,40-byteBITMAPINFOHEADER,24bitBI_RGB,positiveheight,bitsrelativeBMPoffset54. BMPbfSize matchesheader+rowstride*height;2..26zero-paddingbytesfollowBMPwithinNativeData. Descriptors hash complete source stream (including declared native wrapper/padding) and exactBMPspan separately. Decoder21/21AVAILABLE. Independentolefile traversal+BMPbfSize slicing matches extract()21/21exactly. PNGdecodedRGB hashes match independentlyPillow-loadedsourceBMP21/21,0pixelmismatches. This proves decoded sourcebitmapcontent preservation,NOT their Word transforms/compositing/page placement or engineering acceptance.

Evidence:original-stream-inventory.json,original-bitmap-spans.json,original-decoder-checks.json,check_original.py;21derivedPNGinspectionfilesoleObject1.png..oleObject21.png. Nooriginalsourcewrites.

## Bounds and deliberate unavailable cases

SourceOLE<=32MiB;streams<=32;directoryentries<=128;eachstream<=16MiB;aggregatestreambytes<=32MiB;bitmap<=16MiB;pixels<=16000000;nativezero-padding<=64bytes. Beforeoptionalparser:validateCFBv3regularsectorheader,FATextent,finiteacyclicdirectorychain,directoryentrybounds,acyclic/uniquevisiteddirectorytree,miniFATcounts/pointers andoversizedroot/streammetadata. Optionalolefileopenedreadonly withDEFECT_INCORRECT;anyreportedparsingdefects,duplicatecasefoldedstreampaths,wrongstreamlengthfailclosed. Streams are never executed. OnlyrootCONTENTS BMP/DIB or\x01Ole10Native bitmapformrecognized;noarbitrarysignaturesearch/packagedexecutableinterpretation.

UnsupportedCFBv4/extendedDIFAT,compressedBMP,paletteBMP,non40-byteDIBheader,non24/32bitBI_RGB,colorprofiles/masks,nonzerotrailingdata,unknownnested/packageformat yieldUNAVAILABLE. Complete original bytes remain with caller. Optionalolefileabsent→UNAVAILABLE/OLEFILE_UNAVAILABLE;nodependencyinstallation/paidserviceperformedbyproductcode. Duringaudita pinnedolefile0.47wasinstalledonlyinscratchdeps;parentlaterinstalledolefile0.47inruntimeuserpackages. No requirements file edited by this agent.

## Tests

Initial9testsREDbecausemissingproductionmodule(red-tests.log);thenGREEN. AddedmaliciousminiFAT/oversizedrootcaseRED(AVAILABLEincorrectly),hardenedpreflight,now10testsPASS. CoversactualCFBfixtures,exactnativeBMPspan/hash/pixels,DIB/topdownBMP,invalidsource/size,nativelength/truncatedpixels,explicitambiguousselector/streamcount/bytebudgets,pixelbombbeforePillow,unknownexecutablestream/no scanning,directorycycle/duplicatepaths,maliciousminiFAT/rootbounds andsimulatedmissingoptionalmodule. green-tests.log captures all10PASS. Fullprojectunittestdiscover completed:931tests in72.104s,OK(skipped=17),exit0;see full-tests.log. The emitted document-completeness BLOCK line is a workflow test diagnostic,not a unittest failure;it does not grant visual completeness.

## Primary format/API references

https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-oleds/cc825ec3-f0ed-4023-97f6-13c323ac1172 (OLENativeStream,sizeprefixandNativeData)
https://learn.microsoft.com/windows/win32/api/wingdi/ns-wingdi-bitmapfileheader (BMPfileheader,bfOffBits)
https://olefile.readthedocs.io/en/stable/olefile.html (readonlyopenstream,get_size,listdir,DEFECT_INCORRECT)

## Review follow-up multicolor regression

Addedtest_multicolor_rows_preserve_orientation_and_bgr_channels_24_32_bit with4subcases:24/32bit×bottom-up/top-down.41×40pixels vary independently bycolumn,rowandRGBchannel;24-bitrowpaddingisnonzeroand32-bitXbytesare37. Assertions compareeverydecodedRGBbyte withindependentlygeneratedexpectedpixels,plusmode/dimensionsanddeclaredorientation/depth. Focused11testsPASS(exit0). Runtime-onlymutationchecks(non-repositorypatches) invertroworientationandchangeBGR/BGRXtoRGB/RGBX;eachmutationcausesall4subcases tofailwith0errors,provingregressioncoverage. Logs:multicolor-focused-tests.log,multicolor-orientation-mutation.log,multicolor-channels-mutation.log,multicolor-mutation-results.json. No decoderbugfound;productionmoduleunchanged. Fullsuite intentionally not rerun because parent instructedfocusedonlyuntilintegrationfinishes. Nooriginalsourcewrites.
