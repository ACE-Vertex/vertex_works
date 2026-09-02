fn main() {
    #[cfg(windows)]
    {
        embed_resource::compile("app.rc", embed_resource::NONE)
            .manifest_required()
            .expect("failed to embed Vertex Works launcher icon");
    }
}
