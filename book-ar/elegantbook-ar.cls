\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{elegantbook-ar}[2026/07/26 ElegantBook wrapper for Arabic RTL]

% ElegantBook loads biblatex internally. Polyglossia must be loaded first, so
% register it on LaTeX's package hook before delegating to the upstream class.
% fvextra loads lineno later; bidi requires lineno to have been loaded before
% bidi/polyglossia, so keep this ordering dependency in the early hook.
\AddToHook{package/biblatex/before}{%
  \RequirePackage{float}%
  \RequirePackage{lineno}%
  \RequirePackage{polyglossia}%
}
\LoadClassWithOptions{elegantbook}
