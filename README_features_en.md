v0.1.5 (Alpha 1)
Core Engine and GUI: The first functional release, laying the essential groundwork. The browser utilizes the PyFLTK graphical interface and a command system for layout construction.
Basic Text Rendering: Initial handling of HTTP/HTTPS requests with text output. Implemented support for primary block tags: <h1> (headers), <p> (paragraphs), and <section> (structural blocks).
Navigation: Introduced a functional address bar and a basic, minimalistic history saving system, allowing for the first steps in page navigation.

v0.2.0 (Alpha 2)
Interactivity: A pivotal release that transformed the application from a simple viewer into a browser. Added full support for clickable links (<a>), enabling navigation between web pages.
Media and Structure: Introduced support for rendering images (<img>) from external (HTTP/HTTPS) sources and the display of tables (<table>, <tr>, <td>), showcasing the ability to handle complex content.
Session Management: Integrated a full Navigation History Manager with working "Back" and "Forward" buttons, alongside an initial demonstration of Python Ecosystem capabilities (cookies, security checks).

v0.2.5 (Beta 1)
GUI Improvements: Completely revamped navigation panel meeting modern standards: added Refresh (↻) and Home (🏠) buttons. Enhanced "Settings" button functionality, leading to the internal settings page (wind://flags).
Adaptive Layout: The major engine upgrade—implementation of the Dynamic Table Layout. Column widths are now calculated automatically, and the entire table adaptively compresses to guarantee it fits within the rendering window (a key step towards responsive design).
Standards Compliance: Introduced CSS Box Model visualization via borders (border) for block elements. Expanded support for structural HTML5 tags (<div>, <header>, <footer>).
Infrastructure: Full support for internal schemes (wind://) for system and experimental pages. Added the interface theme switching feature (Light/Dark).
