import AppKit
import Foundation
let phase = CommandLine.arguments[1]
let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let folder = root.appendingPathComponent("Saved/Town/session-1/\(phase)")
let files = try FileManager.default.contentsOfDirectory(at:folder,includingPropertiesForKeys:nil).filter{$0.pathExtension == "png"}.sorted{$0.lastPathComponent < $1.lastPathComponent}
precondition(files.count == 10, "Expected all ten fixed views")
let w = 1920, h = 2900
let image = NSImage(size:NSSize(width:w,height:h))
image.lockFocus()
NSColor(calibratedWhite:0.08,alpha:1).setFill();NSRect(x:0,y:0,width:w,height:h).fill()
for (i,file) in files.enumerated() {
 let x=(i%2)*960, y=(4-i/2)*580
 let source=NSImage(contentsOf:file)!
 source.draw(in:NSRect(x:x,y:y+40,width:960,height:540))
 ("\(phase.uppercased()) · \(file.deletingPathExtension().lastPathComponent)" as NSString).draw(at:NSPoint(x:x+14,y:y+9),withAttributes:[.font:NSFont.systemFont(ofSize:22,weight:.medium),.foregroundColor:NSColor.white])
}
image.unlockFocus()
let bitmap=NSBitmapImageRep(data:image.tiffRepresentation!)!
let out=root.appendingPathComponent("Saved/Town/session-1/\(phase)-contact.jpg")
try bitmap.representation(using:.jpeg,properties:[.compressionFactor:0.94])!.write(to:out)
print(out.path)
