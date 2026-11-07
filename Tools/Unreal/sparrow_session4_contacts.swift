// Local review contact sheets only; source screenshots remain unchanged.
import AppKit
import Foundation

let character = CommandLine.arguments[1]
let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let output = root.appendingPathComponent("Saved/Sparrow/session-4")
let input = output.appendingPathComponent("game-" + character)
let files = try FileManager.default.contentsOfDirectory(at: input, includingPropertiesForKeys: nil)
    .filter { $0.pathExtension == "png" }.sorted { $0.lastPathComponent < $1.lastPathComponent }
for start in stride(from: 0, to: files.count, by: 9) {
    let image = NSImage(size: NSSize(width: 1920, height: 1440))
    image.lockFocus()
    NSColor.darkGray.setFill()
    NSRect(x: 0, y: 0, width: 1920, height: 1440).fill()
    for (index, url) in files[start..<min(start + 9, files.count)].enumerated() {
        guard let source = NSImage(contentsOf: url) else { fatalError("Cannot decode " + url.path) }
        let x = CGFloat(index % 3) * 640
        let y = CGFloat(2 - index / 3) * 480
        source.draw(in: NSRect(x: x, y: y + 30, width: 640, height: 450))
        (url.lastPathComponent as NSString).draw(at: NSPoint(x: x + 8, y: y + 4), withAttributes: [
            .font: NSFont.monospacedSystemFont(ofSize: 20, weight: .regular),
            .foregroundColor: NSColor.white
        ])
    }
    image.unlockFocus()
    let bitmap = NSBitmapImageRep(data: image.tiffRepresentation!)!
    let data = bitmap.representation(using: .jpeg, properties: [.compressionFactor: 0.93])!
    let target = output.appendingPathComponent(String(format: "%@-contact-%02d.jpg", character, start / 9 + 1))
    precondition(!FileManager.default.fileExists(atPath: target.path), "Do not overwrite review evidence")
    try data.write(to: target)
    print(target.path)
}
