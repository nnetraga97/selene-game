// Sparrow / hero before / hero after; seven phase rows for one camera angle.
import AppKit
import Foundation
let hero = CommandLine.arguments[1]
let view = CommandLine.arguments[2]
let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let phases = ["idle", "walk", "run", "sprint", "stop", "pivot", "jump"]
let sources = [("Sparrow", "before"), (hero, "before"), (hero, "after-facing")]
let image = NSImage(size: NSSize(width: 1440, height: 3360))
image.lockFocus()
NSColor.darkGray.setFill()
NSRect(x: 0, y: 0, width: 1440, height: 3360).fill()
for (row, phase) in phases.enumerated() {
    for (col, sourceInfo) in sources.enumerated() {
        let (name, label) = sourceInfo
        let filename = String(format: "%02d_%@_%@.png", row, phase, view)
        let url = root.appendingPathComponent("Saved/AnimMatch/Captures/\(label)/\(name)/\(filename)")
        guard let source = NSImage(contentsOf: url) else { fatalError("Missing " + url.path) }
        let x = CGFloat(col) * 480
        let y = CGFloat(6 - row) * 480
        source.draw(in: NSRect(x: x, y: y + 30, width: 480, height: 450))
        ("\(name) \(label) / \(phase)" as NSString).draw(at: NSPoint(x: x + 8, y: y + 7), withAttributes: [.font: NSFont.monospacedSystemFont(ofSize: 15, weight: .regular), .foregroundColor: NSColor.white])
    }
}
image.unlockFocus()
let bitmap = NSBitmapImageRep(data: image.tiffRepresentation!)!
let data = bitmap.representation(using: .jpeg, properties: [.compressionFactor: 0.94])!
let output = root.appendingPathComponent("Saved/AnimMatch/session-1/\(hero)-before-after-\(view).jpg")
precondition(!FileManager.default.fileExists(atPath: output.path), "Immutable evidence")
try data.write(to: output)
print(output.path)
