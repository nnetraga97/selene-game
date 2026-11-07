// Phase rows, front/side/back columns. Source screenshots are never modified.
import AppKit
import Foundation
let hero = CommandLine.arguments[1]
let label = CommandLine.arguments[2]
let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let input = root.appendingPathComponent("Saved/AnimMatch/Captures/\(label)/\(hero)")
let phases = ["start", "start-mid", "stop", "stop-mid", "stop-late", "pivot", "pivot-mid", "pivot-late"]
let indices = [7, 8, 4, 9, 10, 5, 11, 12]
let views = ["front", "side", "back"]
let image = NSImage(size: NSSize(width: 1440, height: 3840))
image.lockFocus()
NSColor.darkGray.setFill()
NSRect(x: 0, y: 0, width: 1440, height: 3840).fill()
for (row, phase) in phases.enumerated() {
    for (col, view) in views.enumerated() {
        let filename = String(format: "%02d_%@_%@.png", indices[row], phase, view)
        let url = input.appendingPathComponent(filename)
        guard let source = NSImage(contentsOf: url) else { fatalError("Missing " + url.path) }
        let x = CGFloat(col) * 480
        let y = CGFloat(7 - row) * 480
        source.draw(in: NSRect(x: x, y: y + 30, width: 480, height: 450))
        ("\(hero) \(label) / \(phase) / \(view)" as NSString).draw(at: NSPoint(x: x + 8, y: y + 7), withAttributes: [.font: NSFont.monospacedSystemFont(ofSize: 16, weight: .regular), .foregroundColor: NSColor.white])
    }
}
image.unlockFocus()
let bitmap = NSBitmapImageRep(data: image.tiffRepresentation!)!
let data = bitmap.representation(using: .jpeg, properties: [.compressionFactor: 0.94])!
let session = CommandLine.arguments.count > 3 ? CommandLine.arguments[3] : "session-3"
let output = root.appendingPathComponent("Saved/AnimMatch/\(session)/\(hero)-\(label)-transitions.jpg")
precondition(!FileManager.default.fileExists(atPath: output.path), "Immutable evidence")
try data.write(to: output)
print(output.path)
