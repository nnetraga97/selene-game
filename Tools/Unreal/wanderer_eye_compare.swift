import AppKit
import Foundation
let root=URL(fileURLWithPath:FileManager.default.currentDirectoryPath)
let base=root.appendingPathComponent("Saved/WandererHookup/session-1")
let files=[("details-canonical/captures/001_front_eyes_01.13.png","Before: kept slot, unsupported skeletal usage"),("details-eyes/captures/001_front_eyes_01.16.png","After: Wanderer-owned skeletal-compatible FoxEye_amber")]
let sheet=NSImage(size:NSSize(width:1280,height:400));sheet.lockFocus();NSColor.darkGray.setFill();NSRect(x:0,y:0,width:1280,height:400).fill()
for (i,entry) in files.enumerated(){
 let source=NSImage(contentsOf:base.appendingPathComponent(entry.0))!
 source.draw(in:NSRect(x:i*640,y:40,width:640,height:360))
 (entry.1 as NSString).draw(at:NSPoint(x:i*640+8,y:12),withAttributes:[.font:NSFont.systemFont(ofSize:14),.foregroundColor:NSColor.white])
}
sheet.unlockFocus();let output=base.appendingPathComponent("Wanderer-eyes-before-after.jpg");precondition(!FileManager.default.fileExists(atPath:output.path));try NSBitmapImageRep(data:sheet.tiffRepresentation!)!.representation(using:.jpeg,properties:[.compressionFactor:0.96])!.write(to:output);print(output.path)
