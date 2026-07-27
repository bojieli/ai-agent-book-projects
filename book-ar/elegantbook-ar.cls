\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{elegantbook-ar}[2026/07/26 ElegantBook wrapper for Arabic RTL]

% ElegantBook loads biblatex internally. Polyglossia must be loaded first, so
% register it on LaTeX's package hook before delegating to the upstream class.
\AddToHook{package/biblatex/before}{%
  \RequirePackage{float}%
  \RequirePackage{lineno}%
  \RequirePackage{polyglossia}%
}
\LoadClassWithOptions{elegantbook}
