// Equal crops, phase samples (not synchronized gait), without altering source screenshots.
import AppKit
import Foundation
let args=CommandLine.arguments
let root=URL(fileURLWithPath:FileManager.default.currentDirectoryPath)
let sources=[(args[1],args[2]),(args[3],args[4])],view=args[5]
let output=URL(fileURLWithPath:args[6]);let phases=["idle","walk","run","sprint","stop","pivot","jump"]
let width=1040,height=7*510
let sheet=NSImage(size:NSSize(width:width,height:height));sheet.lockFocus()
NSColor.darkGray.setFill();NSRect(x:0,y:0,width:width,height:height).fill()
for (row,phase) in phases.enumerated(){
 for (col,info) in sources.enumerated(){
  let (hero,label)=info;let name=String(format:"%02d_%@_%@.png",row,phase,view)
  let url=root.appendingPathComponent("Saved/AnimMatch/Captures/\(label)/\(hero)/\(name)")
  guard let source=NSImage(contentsOf:url) else {fatalError("Missing "+url.path)}
  let x=CGFloat(col*520),y=CGFloat((6-row)*510)
  source.draw(in:NSRect(x:x,y:y+33,width:520,height:477),from:NSRect(x:220,y:230,width:520,height:477),operation:.copy,fraction:1)
  ("\(hero) / \(phase) / \(view) / \(label.contains("YsoldeHookup") ? "prior" : "current")" as NSString).draw(at:NSPoint(x:x+5,y:y+10),withAttributes:[.font:NSFont.monospacedSystemFont(ofSize:12,weight:.regular),.foregroundColor:NSColor.white])
 }
}
sheet.unlockFocus();let b=NSBitmapImageRep(data:sheet.tiffRepresentation!)!
precondition(!FileManager.default.fileExists(atPath:output.path));try b.representation(using:.jpeg,properties:[.compressionFactor:0.95])!.write(to:output);print(output.path)
