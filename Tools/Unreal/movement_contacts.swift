import AppKit
import Foundation

// Usage: swift movement_contacts.swift INPUT_DIRECTORY OUTPUT_JPG [columns]
let input = URL(fileURLWithPath: CommandLine.arguments[1])
let output = URL(fileURLWithPath: CommandLine.arguments[2])
let columns = CommandLine.arguments.count > 3 ? Int(CommandLine.arguments[3])! : 3
let files = try FileManager.default.contentsOfDirectory(at: input, includingPropertiesForKeys: nil)
    .filter { $0.pathExtension.lowercased() == "png" }.sorted { $0.lastPathComponent < $1.lastPathComponent }
precondition(!files.isEmpty && !FileManager.default.fileExists(atPath: output.path), "Missing input or existing evidence")
let rows = (files.count + columns - 1) / columns
let width = columns * 480, height = rows * 480
let image = NSImage(size: NSSize(width: width, height: height))
image.lockFocus()
NSColor.darkGray.setFill()
NSRect(x: 0, y: 0, width: width, height: height).fill()
for (i, file) in files.enumerated() {
    guard let source = NSImage(contentsOf: file) else { fatalError("Unreadable " + file.path) }
    let x = (i % columns) * 480, y = (rows - 1 - i / columns) * 480
    source.draw(in: NSRect(x: x, y: y + 30, width: 480, height: 450))
    (file.deletingPathExtension().lastPathComponent as NSString).draw(at: NSPoint(x: x + 8, y: y + 7),
        withAttributes: [.font: NSFont.monospacedSystemFont(ofSize: 14, weight: .regular), .foregroundColor: NSColor.white])
}
image.unlockFocus()
let bitmap = NSBitmapImageRep(data: image.tiffRepresentation!)!
try bitmap.representation(using: .jpeg, properties: [.compressionFactor: 0.94])!.write(to: output)
print(output.path)
