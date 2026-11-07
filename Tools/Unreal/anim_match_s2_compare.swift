import AppKit
import Foundation
let hero = CommandLine.arguments[1], view = CommandLine.arguments[2]
let current = CommandLine.arguments[3], candidate = CommandLine.arguments[4]
let candidateTitle = CommandLine.arguments.count > 5 ? CommandLine.arguments[5] : "candidate"
let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let phases = ["idle", "walk", "run", "sprint", "stop", "pivot", "jump"]
let sources = [("Sparrow", "before", "Sparrow reference"), (hero, current, "\(hero) current"), (hero, candidate, "\(hero) \(candidateTitle)")]
let image = NSImage(size: NSSize(width: 1080, height: 2520))
image.lockFocus()
NSColor.darkGray.setFill(); NSRect(x:0,y:0,width:1080,height:2520).fill()
for (row, phase) in phases.enumerated() {
 for (col, info) in sources.enumerated() {
  let (name,label,title) = info
  let file = String(format:"%02d_%@_%@.png",row,phase,view)
  let url = root.appendingPathComponent("Saved/AnimMatch/Captures/\(label)/\(name)/\(file)")
  guard let source = NSImage(contentsOf:url) else { fatalError("Missing " + url.path) }
  let x=CGFloat(col)*360, y=CGFloat(6-row)*360
  source.draw(in:NSRect(x:x,y:y+30,width:360,height:330),from:NSRect(x:220,y:230,width:520,height:477),operation:.copy,fraction:1)
  ("\(title) / \(phase)" as NSString).draw(at:NSPoint(x:x+5,y:y+7),withAttributes:[.font:NSFont.monospacedSystemFont(ofSize:13,weight:.regular),.foregroundColor:NSColor.white])
 }
}
image.unlockFocus()
let data=NSBitmapImageRep(data:image.tiffRepresentation!)!.representation(using:.jpeg,properties:[.compressionFactor:0.94])!
let out=root.appendingPathComponent("Saved/AnimMatch/session-2/\(hero)-\(current)-vs-\(candidate)-\(view).jpg")
precondition(!FileManager.default.fileExists(atPath:out.path));try data.write(to:out);print(out.path)
