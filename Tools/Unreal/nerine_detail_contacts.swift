import AppKit
import Foundation
let root=URL(fileURLWithPath:FileManager.default.currentDirectoryPath)
let label=CommandLine.arguments.count > 2 ? CommandLine.arguments[2] : "details-eyes"
let input=root.appendingPathComponent("Saved/NerineHookup/session-1/Nerine/\(label)/captures")
let view=CommandLine.arguments[1]
let output=root.appendingPathComponent("Saved/NerineHookup/session-1/Nerine/Nerine-\(label)-\(view).jpg")
let files=try FileManager.default.contentsOfDirectory(at:input,includingPropertiesForKeys:nil).filter{$0.pathExtension=="png" && $0.lastPathComponent.contains("_\(view)_")}.sorted{$0.lastPathComponent<$1.lastPathComponent}
precondition(!files.isEmpty)
let cols=3,rows=(files.count+cols-1)/cols,w=cols*640,h=rows*400
let sheet=NSImage(size:NSSize(width:w,height:h));sheet.lockFocus();NSColor.darkGray.setFill();NSRect(x:0,y:0,width:w,height:h).fill()
for (i,file) in files.enumerated(){
 let image=NSImage(contentsOf:file)!;let x=(i%cols)*640,y=(rows-1-i/cols)*400
 image.draw(in:NSRect(x:x,y:y+40,width:640,height:360))
 (file.deletingPathExtension().lastPathComponent as NSString).draw(at:NSPoint(x:x+8,y:y+12),withAttributes:[.font:NSFont.monospacedSystemFont(ofSize:17,weight:.regular),.foregroundColor:NSColor.white])
}
sheet.unlockFocus();precondition(!FileManager.default.fileExists(atPath:output.path));try NSBitmapImageRep(data:sheet.tiffRepresentation!)!.representation(using:.jpeg,properties:[.compressionFactor:0.96])!.write(to:output);print(output.path)
