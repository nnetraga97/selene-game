import AppKit
import Foundation
let root=URL(fileURLWithPath:FileManager.default.currentDirectoryPath)
let folder=CommandLine.arguments.count>1 ? CommandLine.arguments[1] : "session-1"
let dir=root.appendingPathComponent("Saved/SlidePass/\(folder)")
let heroes=["Champion","Angel","Sparrow","Fixer","Courier","Fox","Wanderer","Ysolde","Nerine","Base"]
let phases=["run","into","loop","out_run","resume_run","out_stand","stand"]
func write(_ filename:String,_ rows:[String],_ cols:[(String,String)]) throws {
 let w=280,h=302,header=38,width=cols.count*w,height=rows.count*h+header
 let sheet=NSImage(size:NSSize(width:width,height:height));sheet.lockFocus()
 NSColor(calibratedWhite:0.09,alpha:1).setFill();NSRect(x:0,y:0,width:width,height:height).fill()
 ("GASP slide candidates / \(folder) / sampled native slot poses / continuity not certified" as NSString).draw(at:NSPoint(x:12,y:height-27),withAttributes:[.font:NSFont.systemFont(ofSize:18,weight:.bold),.foregroundColor:NSColor.white])
 for (row,hero) in rows.enumerated(){for (col,info) in cols.enumerated(){
  let (view,phase)=info
  let sourceURL=dir.appendingPathComponent("captures/\(hero)_\(view)_\(phase).png")
  guard let source=NSImage(contentsOf:sourceURL) else {fatalError("Missing "+sourceURL.path)}
  let x=col*w,y=(rows.count-1-row)*h
  source.draw(in:NSRect(x:x,y:y+22,width:w,height:w),from:.zero,operation:.copy,fraction:1)
  ("R\(row+1) C\(col+1) \(hero) / \(view) / \(phase)" as NSString).draw(at:NSPoint(x:x+4,y:y+5),withAttributes:[.font:NSFont.monospacedSystemFont(ofSize:10,weight:.medium),.foregroundColor:NSColor.white])
 }}
 sheet.unlockFocus();let bmp=NSBitmapImageRep(data:sheet.tiffRepresentation!)!
 try bmp.representation(using:.jpeg,properties:[.compressionFactor:0.92])!.write(to:dir.appendingPathComponent(filename))
 print(dir.appendingPathComponent(filename).path)
}
try write("slides-side.jpg",heroes,phases.map{("side",$0)})
try write("slides-front.jpg",heroes,phases.map{("front",$0)})
try write("slides-all-heroes.jpg",heroes,["side","front"].flatMap{view in phases.map{(view,$0)}})
try write("regression.jpg",["Ysolde","Sparrow"],["side","front"].flatMap{view in ["walk","run","sprint","jump"].map{(view,"regression_"+$0)}})
