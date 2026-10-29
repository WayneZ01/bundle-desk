import AppKit
import Foundation

let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let output = root.appendingPathComponent("mac/assets/BundleDesk.iconset")
try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
func color(_ hex: UInt32) -> NSColor {
    NSColor(srgbRed: CGFloat((hex >> 16) & 255)/255, green: CGFloat((hex >> 8) & 255)/255, blue: CGFloat(hex & 255)/255, alpha: 1)
}
func polygon(_ points: [(CGFloat, CGFloat)], fill: NSColor) {
    let p=NSBezierPath();p.move(to:NSPoint(x:points[0].0,y:points[0].1))
    for v in points.dropFirst(){p.line(to:NSPoint(x:v.0,y:v.1))};p.close();fill.setFill();p.fill()
}
func render(_ size: Int) -> Data {
    let bitmap=NSBitmapImageRep(bitmapDataPlanes:nil,pixelsWide:size,pixelsHigh:size,bitsPerSample:8,samplesPerPixel:4,hasAlpha:true,isPlanar:false,colorSpaceName:.deviceRGB,bytesPerRow:0,bitsPerPixel:0)!
    NSGraphicsContext.saveGraphicsState(); NSGraphicsContext.current=NSGraphicsContext(bitmapImageRep:bitmap)
    let context=NSGraphicsContext.current!.cgContext
    context.scaleBy(x:CGFloat(size)/1024,y:CGFloat(size)/1024)
    let tile=NSBezierPath(roundedRect:NSRect(x:100,y:100,width:824,height:824),xRadius:184,yRadius:184)
    NSGraphicsContext.saveGraphicsState()
    let shadow=NSShadow();shadow.shadowColor=NSColor.black.withAlphaComponent(0.22);shadow.shadowBlurRadius=23;shadow.shadowOffset=NSSize(width:0,height:-13);shadow.set()
    color(0x205c49).setFill();tile.fill();NSGraphicsContext.restoreGraphicsState()
    NSGradient(starting:color(0x377c60),ending:color(0x123f34))!.draw(in:tile,angle:-65)
    let inset=NSBezierPath(roundedRect:NSRect(x:102,y:102,width:820,height:820),xRadius:182,yRadius:182)
    NSColor.white.withAlphaComponent(0.13).setStroke();inset.lineWidth=3;inset.stroke()
    // A phone, with a quiet screen and bright frame.
    let phone=NSBezierPath(roundedRect:NSRect(x:557,y:249,width:221,height:489),xRadius:44,yRadius:44)
    NSColor.white.withAlphaComponent(0.95).setFill();phone.fill()
    let screen=NSBezierPath(roundedRect:NSRect(x:577,y:271,width:181,height:443),xRadius:27,yRadius:27)
    color(0x1e5442).setFill();screen.fill()
    let speaker=NSBezierPath(roundedRect:NSRect(x:633,y:685,width:70,height:10),xRadius:5,yRadius:5)
    color(0xafd4b5).setFill();speaker.fill()
    let home=NSBezierPath(roundedRect:NSRect(x:640,y:286,width:55,height:7),xRadius:3,yRadius:3)
    NSColor.white.withAlphaComponent(0.6).setFill();home.fill()
    // Isometric application bundle, with a folded top.
    polygon([(240,570),(386,650),(529,570),(386,487)],fill:color(0xd6eb9d))
    polygon([(240,570),(386,487),(386,308),(240,394)],fill:color(0xa8ce72))
    polygon([(386,487),(529,570),(529,394),(386,308)],fill:color(0x7eae62))
    polygon([(301,604),(447,522),(447,477),(417,460),(417,505),(271,587)],fill:color(0xebf5c7))
    // Delivery arrow follows the bundle to the phone.
    let arrow=NSBezierPath();arrow.move(to:NSPoint(x:444,y:430));arrow.line(to:NSPoint(x:670,y:430))
    arrow.lineWidth=42;arrow.lineCapStyle = .round;NSColor.white.setStroke();arrow.stroke()
    let tip=NSBezierPath();tip.move(to:NSPoint(x:620,y:482));tip.line(to:NSPoint(x:673,y:430));tip.line(to:NSPoint(x:620,y:378));tip.lineWidth=39;tip.lineCapStyle = .round;tip.lineJoinStyle = .round;tip.stroke()
    NSGraphicsContext.restoreGraphicsState()
    return bitmap.representation(using:.png,properties:[:])!
}
for size in [16,32,128,256,512] {
    try render(size).write(to:output.appendingPathComponent("icon_\(size)x\(size).png"))
    try render(size*2).write(to:output.appendingPathComponent("icon_\(size)x\(size)@2x.png"))
}
try render(1024).write(to:root.appendingPathComponent("mac/assets/BundleDesk.png"))
